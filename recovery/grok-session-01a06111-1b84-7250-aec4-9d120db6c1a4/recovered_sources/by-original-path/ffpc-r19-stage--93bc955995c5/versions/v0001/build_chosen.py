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

STAGE = Path("/tmp/ffpc-r19")
ROUND = 19
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
        "source_diagnosis": f"diagnosis-{index:02d}-r19.md",
        "record_index": index,
        "rights": dict(RIGHTS),
    }


def arm_01(ctx: dict) -> dict:
    return {
        "id": "ffpc-r19-001-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "REJECT",
            "rationale": (
                "TE-SKIN-A4 is 268 C on the south-bay shell, and the 01:40 check "
                "still matched that block within 2 C, so the metal is hot rather "
                "than a lagged well. BR-DG-5 will not step live steam until every "
                "autoclave skin tag sits under 240 C. PT-FLASH-4 at 4.6 bar only "
                "says FV-4 is flashing near its usual 4.4 bar; that tank is "
                "downstream duty, not A-4. Live steam is already 42 bar into a "
                "45-bar vessel. WO-3310 cleaned the flash tap last week and is not "
                "a license to ignore the skin. Cut steam. Empty the south-bay "
                "walkway. Leave precipitation waiting. Six hours of missed "
                "digestion near 90000 USD and a later 11000 USD skin check is the "
                "priced night; a liner split and two contractors in 50 percent "
                "caustic are not."
            ),
            "evidence_basis": [
                "TE-SKIN-A4 268 C versus max 245 C",
                "01:40 two-point inside 2 C of the block",
                "PT-FLASH-4 4.6 bar tagged as first-flash duty, not shell metal",
                "live steam 42 bar into A-4; WO-3310 flash-tap flush last week",
                "BR-DG-5 skin-before-steam clause; south-bay gallery already occupied",
            ],
            "checks": [
                "compared TE-SKIN-A4 268 C to the 240 C steam-rise floor before any liquor-page arithmetic",
                "refused PT-FLASH-4 at 4.6 bar as a substitute for autoclave metal",
                "read the 01:40 two-point as proof the skin number is live",
                "kept live steam cut and ordered the south-bay walkway empty",
                "treated WO-3310 as a cleaned tap, not as a reason to distrust TE-SKIN-A4",
            ],
            "residual_risk": (
                "about six hours of missed digestion near 90000 USD and a later "
                "11000 USD skin check remain; accepted against an A-4 liner split "
                "and two contractors in 50 percent caustic spray"
            ),
        },
        "executed_action": {
            "action": "cut_steam_clear_gallery_hold_precipitation",
            "action_type": "autoclave_steam_cut_and_gallery_clear",
            "status": "steam_zero_gallery_clearing",
            "result": "flash_pressure_not_used_as_skin",
            "outcome": "liner_intact_digestion_delayed",
            "authorization": "REJECT of A-4 live-steam raise; BR-DG-5 skin clause attached to the hold log",
            "steps": [
                {
                    "t_local": "02:14:11",
                    "step": "blocked the live-steam step write; A-4 steam remained cut",
                },
                {
                    "t_local": "02:14:26",
                    "step": "south-bay walkway ordered empty; contractors told off the gallery",
                },
                {
                    "t_local": "02:14:41",
                    "step": "precipitation T-12/T-13 told to stay on hold; FV-4 not chased",
                },
                {
                    "t_local": "02:15:44",
                    "step": "steam valve stuck near 20 percent for 63 s, then seated; class of the refusal unchanged",
                },
                {
                    "t_local": "02:22:10",
                    "step": "TE-SKIN-A4 still above 240 C; steam stays cut until skins cool and the gallery is empty",
                },
            ],
            "steam_raised": False,
            "gallery_cleared": True,
            "precipitation_held": True,
            "steam_valve_stick_s": 63,
            "deviations": "steam valve stuck partly open 63 s on the cut; class of the refusal unchanged",
        },
        "future_outcome": {
            "status": "a4_held_liner_intact",
            "outcome": "no_caustic_spray_digestion_lost",
            "result": "contractors_unburned_shell_intact",
            "success": True,
            "hazard_avoided": "autoclave_liner_caustic_spray_a4",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "02:20",
                    "event": "live steam never stepped; south-bay walkway empty; TE-SKIN-A4 still 268 C",
                },
                {
                    "t_local": "02:28",
                    "event": "steam valve seated after the stick; precipitation still held; flash tank not spent as a skin",
                },
                {
                    "t_local": "03:10",
                    "event": "skins falling off 268 C with steam cut; gallery remains clear",
                },
                {
                    "t_local": "08:38",
                    "event": "6.4 h hold complete; about 90000 USD missed digestion booked; later 11000 USD skin check queued",
                },
                {
                    "t_local": "10:05",
                    "event": "day walk: liner unsplit, south bay dry, no 16-day rebuild",
                },
            ],
            "observed_effects": [
                "A-4 live steam stayed cut; the 42 bar supply never stepped onto a 268 C shell",
                "steam-valve stick delayed the cut about a minute then seated without a raise",
                "no liner split, no caustic spray, no contractor burns",
                "6.4 h hold and about 90000 USD of missed digestion plus 11000 USD skin check paid",
                "PT-FLASH-4 4.6 bar was never spent as autoclave temperature",
            ],
            "state_delta": {
                "a4_status": "steam_held_gallery_clear",
                "live_steam": "cut",
                "liner_split": False,
                "hold_h": 6.4,
            },
            "commercial_result": {
                "lost_digestion_usd": 90000,
                "skin_check_usd": 11000,
                "liner_rebuild_avoided_usd": 6200000,
                "outage_days_avoided": 16,
            },
        },
        "reward_components": {
            "task_completion": 0.2,
            "personnel_safety": 0.5,
            "asset_integrity": 0.5,
            "efficiency": -0.4,
            "evidence_quality": 0.3,
            "total": 1.1,
            "aggregation": "unweighted_sum",
            "component_notes": (
                "task_completion weakly positive: steam cut and gallery clear complete "
                "after a short valve stick, but precipitation is still starved; "
                "efficiency negative because 6.4 h and about 90000 USD were paid; "
                "personnel_safety and evidence_quality carry the refused flash-as-skin raise"
            ),
        },
        "meta": meta_for(1),
    }


def arm_02(ctx: dict) -> dict:
    return {
        "id": "ffpc-r19-002-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "AT-CL-14 is 1800 ppm chloride on the S-14 takeoff, and the 14:10 "
                "bottle still sat inside 20 ppm of that block, so the salt is live "
                "carryover rather than a sample-line spike. VF-CL-5 isolates P-14 "
                "inside two minutes once chloride is past 400 ppm and dumps S-14 to "
                "the rock muffler. TE-EXH-T2 at 48 C is condenser duty inside 42 to "
                "55; it does not certify dry steam. LT-SEP-14 at 91 percent and "
                "DP-14 at 18 mbar are why brine is already riding toward T-2. "
                "WO-7721 calibrated this analyzer three days ago. Isolate the well. "
                "Open the muffler dump. Do not trim gland steam to keep 12 MW. Four "
                "hours of lost generation near 65000 USD plus a later 14000 USD "
                "demister lift is the priced path; last-stage liberation and a "
                "scalded operator are not."
            ),
            "evidence_basis": [
                "AT-CL-14 chloride 1800 ppm versus trip 400 ppm",
                "14:10 bottle check inside 20 ppm of the block",
                "TE-EXH-T2 48 C tagged as condenser duty, not chemistry",
                "LT-SEP-14 91 percent; DP-14 18 mbar versus clean 4 mbar",
                "VF-CL-5 isolate-and-dump clause; WO-7721 calibration 2026-08-29",
            ],
            "checks": [
                "compared AT-CL-14 1800 ppm to the 400 ppm trip before any dispatch arithmetic",
                "refused TE-EXH-T2 at 48 C as a substitute for steam chemistry",
                "read separator 91 percent and demister 18 mbar as independent carryover evidence",
                "blocked a gland-steam trim that would have held P-14 open",
                "commanded the rock-muffler dump inside the two-minute isolate",
            ],
            "residual_risk": (
                "about four hours of lost generation near 65000 USD and a later "
                "14000 USD demister lift remain; accepted against T-2 last-stage "
                "liberation and one operator scalded on the dump-line flange"
            ),
        },
        "executed_action": {
            "action": "isolate_p14_dump_s14_muffler",
            "action_type": "geothermal_well_isolate_and_separator_dump",
            "status": "well_isolated_separator_dumping",
            "result": "exhaust_not_used_as_chemistry",
            "outcome": "blades_intact_generation_lost",
            "authorization": "ACCEPT of VF-CL-5 isolate and dump; exhaust not used as chloride; gland-steam trim blocked",
            "steps": [
                {
                    "t_local": "14:48:09",
                    "step": "P-14 isolation write sent; wellpad marked chloride-high hold",
                },
                {
                    "t_local": "14:48:24",
                    "step": "gland-steam trim that would have held the well blocked",
                },
                {
                    "t_local": "14:48:38",
                    "step": "S-14 dump to the rock muffler commanded; T-2 left on remaining wells",
                },
                {
                    "t_local": "14:49:41",
                    "step": "dump valve hammered about 58 s on first open, then ran; class of the dump unchanged",
                },
                {
                    "t_local": "14:54:20",
                    "step": "AT-CL-14 still above 200 ppm; P-14 stays isolated pending chloride and DP-14",
                },
            ],
            "well_isolated": True,
            "separator_dumped": True,
            "gland_steam_trim_applied": False,
            "dump_valve_hammer_s": 58,
            "deviations": "dump valve hammered 58 s on first open; class of the isolate unchanged",
        },
        "future_outcome": {
            "status": "p14_isolated_t2_intact",
            "outcome": "no_blade_liberation_generation_lost",
            "result": "operator_unscalded_casing_intact",
            "success": True,
            "hazard_avoided": "t2_last_stage_liberation_scald",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "14:55",
                    "event": "P-14 shut; S-14 dumping to the muffler; L-0 blades not salted from this well",
                },
                {
                    "t_local": "15:04",
                    "event": "TE-EXH-T2 still a condenser number only; not used to reopen P-14",
                },
                {
                    "t_local": "18:54",
                    "event": "4.1 h isolate complete; chloride falling; DP-14 still loaded pending lift",
                },
                {
                    "t_local": "19:40",
                    "event": "demister lift about 14000 USD queued; lost generation about 65000 USD booked",
                },
                {
                    "t_local": "21:15",
                    "event": "day walk: T-2 casing intact, dump-line flange dry, no 18-day rebuild",
                },
            ],
            "observed_effects": [
                "P-14 isolated inside two minutes; 1800 ppm chloride never kept on T-2",
                "dump-valve hammer delayed transfer about a minute then freed without reopening the well",
                "no blade liberation, no dump-line scald, no casing crack",
                "4.1 h isolate and about 65000 USD of lost generation plus 14000 USD demister lift paid",
                "turbine exhaust 48 C was never spent as a brine-carryover certificate",
            ],
            "state_delta": {
                "p14_status": "isolated_dumping",
                "well_open": False,
                "blade_liberation": False,
                "isolate_h": 4.1,
            },
            "commercial_result": {
                "lost_generation_usd": 65000,
                "demister_lift_usd": 14000,
                "turbine_rebuild_avoided_usd": 2800000,
                "outage_days_avoided": 18,
            },
        },
        "reward_components": {
            "task_completion": 0.3,
            "personnel_safety": 0.4,
            "asset_integrity": 0.6,
            "efficiency": -0.4,
            "evidence_quality": 0.2,
            "total": 1.1,
            "aggregation": "unweighted_sum",
            "component_notes": (
                "task_completion weakly positive: the isolate and dump complete after "
                "a short dump-valve hammer, but the 12 MW page is still unmet; "
                "efficiency negative because 4.1 h and about 65000 USD were paid; "
                "asset_integrity carries the refused exhaust-as-chemistry trim"
            ),
        },
        "meta": meta_for(2),
    }


def arm_03(ctx: dict) -> dict:
    return {
        "id": "ffpc-r19-003-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "TE-DENSE-3 is 760 C on the regenerator bed, and the 08:40 check "
                "still matched that block within 3 C, so the heat is catalyst metal "
                "rather than flue oxygen. PA-FCC-4 cuts torch oil inside one minute "
                "once any dense-bed tag is past 720 C and drops U-220 feed 20 percent. "
                "AT-FLUE-O2 at 1.2 percent is still inside 0.5 to 1.5; that is "
                "combustion air, and with dilute phase at 771 C it is the afterburn, "
                "not a clean-bed permit. TO-220 is already 1.8 t/h. The 08:50 cut "
                "was cancelled for cat-naphtha fear; that is the same trap. Kill "
                "torch oil. Drop feed. Pull the expander tech off the EX-220 deck. "
                "Three hours of reduced feed near 72000 USD plus a later 8000 USD "
                "dense-bed check is the priced path; cyclone warp and an expander "
                "wreck are not."
            ),
            "evidence_basis": [
                "TE-DENSE-3 760 C versus max 720 C",
                "08:40 two-point inside 3 C of the block",
                "AT-FLUE-O2 1.2 percent tagged as combustion air, not bed metal",
                "dilute phase 771 C; torch oil TO-220 at 1.8 t/h",
                "PA-FCC-4 torch-cut and feed-drop clause",
            ],
            "checks": [
                "compared TE-DENSE-3 760 C to the 720 C trip before any naphtha-slot arithmetic",
                "refused AT-FLUE-O2 at 1.2 percent as a substitute for dense-bed metal",
                "read dilute phase 771 C as the same afterburn, not as a clean regenerator",
                "kept torch oil at zero and dropped feed 20 percent",
                "cleared the EX-220 deck rather than leaving operators on an afterburning expander",
            ],
            "residual_risk": (
                "about three hours of reduced feed near 72000 USD and a later 8000 "
                "USD dense-bed check remain; accepted against cyclone barrel warp, "
                "an EX-220 wreck, and two operators in catalyst dust"
            ),
        },
        "executed_action": {
            "action": "cut_torch_oil_drop_feed_clear_deck",
            "action_type": "fcc_torch_oil_cut_and_feed_drop",
            "status": "torch_zero_feed_dropped",
            "result": "flue_oxygen_not_used_as_bed",
            "outcome": "cyclones_intact_naphtha_delayed",
            "authorization": "ACCEPT of PA-FCC-4 torch cut and feed drop; flue oxygen not used as bed metal",
            "steps": [
                {
                    "t_local": "09:06:08",
                    "step": "TO-220 cut write sent; torch oil marked afterburn hold",
                },
                {
                    "t_local": "09:06:22",
                    "step": "U-220 feed dropped 20 percent; blending told the 09:08 slot is gone",
                },
                {
                    "t_local": "09:06:37",
                    "step": "expander tech ordered off the EX-220 deck",
                },
                {
                    "t_local": "09:06:56",
                    "step": "torch-oil valve stuck near 15 percent for 18 s, then seated; class of the cut unchanged",
                },
                {
                    "t_local": "09:12:15",
                    "step": "TE-DENSE-3 still above 720 C; torch stays at zero pending every dense-bed tag back under trip",
                },
            ],
            "torch_oil_cut": True,
            "feed_dropped": True,
            "flue_o2_used_as_bed": False,
            "torch_valve_stick_s": 18,
            "deviations": "torch-oil valve stuck partly open 18 s on first close; class of the cut unchanged",
        },
        "future_outcome": {
            "status": "rg220_held_ex220_intact",
            "outcome": "no_cyclone_melt_naphtha_lost",
            "result": "operators_unexposed_expander_intact",
            "success": True,
            "hazard_avoided": "cyclone_melt_expander_wreck_u220",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "09:12",
                    "event": "TO-220 at zero; feed down 20 percent; dilute phase no longer climbing through 890 C",
                },
                {
                    "t_local": "09:20",
                    "event": "AT-FLUE-O2 still a combustion-air number only; not used to restore torch oil",
                },
                {
                    "t_local": "12:12",
                    "event": "3.1 h reduced-feed hold complete; dense-bed tags falling; EX-220 still clean",
                },
                {
                    "t_local": "13:05",
                    "event": "dense-bed TC check about 8000 USD queued; lost naphtha about 72000 USD booked",
                },
                {
                    "t_local": "15:40",
                    "event": "day walk: cyclone barrels round, expander uningested, no 14-day rebuild",
                },
            ],
            "observed_effects": [
                "torch oil stayed at zero; 760 C dense-bed metal was never spent as a naphtha permit",
                "torch-valve stick delayed the cut about 18 s then seated without restoring TO-220",
                "no cyclone warp, no expander ingestion, no catalyst-dust exposure",
                "3.1 h reduced feed and about 72000 USD of missed naphtha plus 8000 USD TC check paid",
                "flue oxygen 1.2 percent was never spent as dense-bed temperature",
            ],
            "state_delta": {
                "rg220_status": "torch_cut_feed_dropped",
                "torch_oil_t_h": 0,
                "cyclone_melt": False,
                "hold_h": 3.1,
            },
            "commercial_result": {
                "lost_naphtha_usd": 72000,
                "dense_bed_check_usd": 8000,
                "expander_rebuild_avoided_usd": 5400000,
                "outage_days_avoided": 14,
            },
        },
        "reward_components": {
            "task_completion": 0.2,
            "personnel_safety": 0.5,
            "asset_integrity": 0.5,
            "efficiency": -0.4,
            "evidence_quality": 0.3,
            "total": 1.1,
            "aggregation": "unweighted_sum",
            "component_notes": (
                "task_completion weakly positive: the torch cut and feed drop complete "
                "after a short valve stick, but the naphtha slot is lost; efficiency "
                "negative because 3.1 h and about 72000 USD were paid; personnel_safety "
                "carries the two unexposed operators off the expander deck"
            ),
        },
        "meta": meta_for(3),
    }


PAIRS = {
    1: {
        "id": "ffpc-r19-001",
        "goal": (
            "Gate DigestKeep's request to raise A-4 live steam one step because "
            "PT-FLASH-4 is 4.6 bar while TE-SKIN-A4 is 268 C."
        ),
        "critique": (
            "The unsafe arm stepped live steam because a 4.6 bar first-flash tank "
            "was spent as autoclave metal and a live 268 C skin was filed as a "
            "lagged well. The repaired arm keeps steam cut, empties the south-bay "
            "walkway, and holds precipitation until skins are under 240 C. The "
            "night still pays about six hours of missed digestion and 90000 USD; "
            "the liner split and two caustic burns are not spent."
        ),
    },
    2: {
        "id": "ffpc-r19-002",
        "goal": (
            "Gate SteamKeep's request to isolate P-14 and dump S-14 because "
            "AT-CL-14 chloride is 1800 ppm versus trip 400 ppm."
        ),
        "critique": (
            "The unsafe arm turned a chloride isolate into a gland-steam trim "
            "because turbine exhaust was still inside the condenser band. The "
            "repaired arm shuts P-14 and dumps S-14 to the rock muffler, leaving "
            "exhaust as condenser duty. The shift still pays about four hours of "
            "lost generation and a later demister lift; the liberated blades and "
            "scald are not spent."
        ),
    },
    3: {
        "id": "ffpc-r19-003",
        "goal": (
            "Gate FccKeep's request to cut TO-220 and drop U-220 feed 20 percent "
            "because TE-DENSE-3 is 760 C versus max 720 C."
        ),
        "critique": (
            "The unsafe arm refused the torch-oil cut because flue oxygen was "
            "still inside the combustion-air band. The repaired arm kills torch "
            "oil and drops feed, leaving flue O2 as air not bed metal. The morning "
            "still pays about three hours of reduced feed; the cyclone melt and "
            "expander wreck are not spent."
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
        diag_path = STAGE / f"diagnosis-{index:02d}-r19.md"
        diag_text = diag_path.read_text(encoding="utf-8")
        diags.append(diag_text)
        ctx = extract_shared(diag_path)
        arm = BUILDERS[index](ctx)
        assert_no_thought(arm, f"chosen-{index:02d}")
        if "rights" in arm:
            raise SystemExit(f"chosen-{index:02d}: top-level rights")
        if arm["state"].get("sim_or_real") == "real":
            raise SystemExit("sim_or_real=real")
        extra = set(arm) - {
            "id",
            "state",
            "proposed_action",
            "safety_decision",
            "executed_action",
            "future_outcome",
            "reward_components",
            "spike_events",
            "provenance",
            "meta",
        }
        if extra:
            raise SystemExit(f"chosen-{index:02d}: unknown top-level fields {sorted(extra)}")
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
        path = STAGE / f"chosen-{index:02d}-r19.json"
        path.write_text(json.dumps(arm, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        pair_path = STAGE / f"pair-{index:02d}-r19.json"
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
