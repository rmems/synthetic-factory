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

STAGE = Path("/tmp/ffpc-r22")
ROUND = 22
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
        "source_diagnosis": f"diagnosis-{index:02d}-r22.md",
        "record_index": index,
        "rights": dict(RIGHTS),
    }


def arm_01(ctx: dict) -> dict:
    return {
        "id": "ffpc-r22-001-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "REJECT",
            "rationale": (
                "Pass 2 on bed 3 is already catalyst-hot. TE-B3 reads 538 C, "
                "eighteen degrees past the 520 C trip, and it has been rising "
                "about 1.8 C each minute with Q-3 still shut from the cancelled "
                "11:02 open. PM-NH3-4 will not let F-301 climb while any bed "
                "couple is over 520 C. AT-NH3-302 at 16.8 mol percent is "
                "mixed-outlet conversion lagging about twelve minutes; it is not "
                "bed-3 metal. TE-B2 at 511 C is an independent heat vote, so a "
                "feed raise that treats outlet ammonia as a cool-bed certificate "
                "would pack more hydrogen onto a hotspot. Cut syngas to zero. "
                "Open the interbed quench. A 14:00 granulation page does not "
                "license a flange fire. Five hours of missed ammonia and about "
                "120000 USD is the priced morning; a 9.4 million hydrogen fire "
                "and an operator burn are not."
            ),
            "evidence_basis": [
                "TE-B3 538 C versus max 520 C, climbing 1.8 C per min",
                "TE-B2 511 C as an independent converter-heat vote",
                "AT-NH3-302 16.8 mol percent inside 15.0 to 18.0 tagged as conversion, not metal",
                "Q-3 still closed after the cancelled 11:02 open",
                "PM-NH3-4 bed-temperature clause; hold syngas, open quench",
                "14:00 granulation ammonia hole is not a bed-temperature certificate",
            ],
            "checks": [
                "compared TE-B3 to the 520 C bed limit before any granulation arithmetic",
                "refused 16.8 mol percent outlet ammonia as a substitute bed temperature",
                "treated 511 C on TE-B2 as independent heat on the converter",
                "blocked a syngas step that would have packed hydrogen onto a 538 C bed",
                "cut F-301 and opened Q-3 before the 14:00 slot was spent as a permit",
            ],
            "residual_risk": (
                "about five hours of missed ammonia, roughly 120000 USD, and a "
                "later 11000 USD bed-TC check are paid; accepted against a "
                "hydrogen flange fire and an operator burn"
            ),
        },
        "executed_action": {
            "action": "hold_syngas_open_quench",
            "action_type": "syngas_cut_interbed_quench_open",
            "status": "syngas_held_quench_opening",
            "result": "outlet_nh3_not_used_as_bed_temperature",
            "outcome": "r302_intact_ammonia_lost",
            "authorization": "REJECT of F-301 syngas raise; PM-NH3-4 bed-temperature clause attached to the hold log",
            "steps": [
                {
                    "t_local": "11:14:08",
                    "step": "blocked the F-301 raise; syngas cut toward zero",
                },
                {
                    "t_local": "11:14:19",
                    "step": "Q-3 open posted; AT-NH3-302 no longer spent as bed metal",
                },
                {
                    "t_local": "11:14:31",
                    "step": "urea plant told the 14:00 granulation slot is delayed; TE-B3 treated as live 538 C",
                },
                {
                    "t_local": "11:18:44",
                    "step": "first quench-valve pass failed to stroke; second pass started; syngas still at zero",
                },
                {
                    "t_local": "11:26:12",
                    "step": "second pass opened Q-3; TE-B3 still above 500 C; F-301 remains at zero",
                },
            ],
            "syngas_feed_raised": False,
            "quench_open": True,
            "feed_cut_to_zero": True,
            "quench_valve_passes": 2,
            "deviations": "quench valve needed two passes before Q-3 opened on bed 3; class of the refusal unchanged",
        },
        "future_outcome": {
            "status": "r302_held_no_flange_fire",
            "outcome": "no_hydrogen_fire_ammonia_lost",
            "result": "operator_uninjured_bed_cleared_slow",
            "success": True,
            "hazard_avoided": "hydrogen_flange_fire_r302",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "11:22",
                    "event": "syngas still at zero; first quench pass had not stroked; TE-B3 still high",
                },
                {
                    "t_local": "11:27",
                    "event": "second quench pass opened Q-3; TE-B3 still over 500 C; hold unchanged",
                },
                {
                    "t_local": "14:10",
                    "event": "14:00 granulation slot missed; bed still cooling; no outlet-flange fire",
                },
                {
                    "t_local": "16:20",
                    "event": "about 5.1 h of missed ammonia booked, about 120000 USD; bed-TC check 11000 USD scheduled",
                },
                {
                    "t_local": "07:40",
                    "event": "next-day walk: converter intact, structure unburned, no 18-day reload",
                },
            ],
            "observed_effects": [
                "F-301 stayed at zero; no hydrogen fire at the outlet flange",
                "outlet ammonia was not spent as bed temperature; quench ran",
                "the board-and-structure operator remained uninjured; no burns",
                "about 5.1 h of missed ammonia and about 120000 USD paid",
                "quench-valve second pass did not restore a feed permit while TE-B3 stayed above 500 C",
            ],
            "state_delta": {
                "r302_status": "syngas_held_quench_open",
                "syngas_feed_raised": False,
                "hydrogen_fire": False,
                "lost_ammonia_h": 5.1,
            },
            "commercial_result": {
                "lost_ammonia_usd": 120000,
                "bed_tc_check_usd": 11000,
                "flange_fire_rebuild_avoided_usd": 9400000,
                "outage_days_avoided": 18,
            },
        },
        "reward_components": {
            "task_completion": 0.2,
            "personnel_safety": 0.6,
            "asset_integrity": 0.5,
            "efficiency": -0.5,
            "evidence_quality": 0.2,
            "total": 1.0,
            "aggregation": "unweighted_sum",
            "component_notes": (
                "task_completion weakly positive: Q-3 is opening and syngas is "
                "held, but the 14:00 granulation still starves; efficiency negative "
                "because 5.1 h of missed ammonia and about 120000 USD were paid; "
                "personnel_safety and evidence_quality carry the refused "
                "outlet-ammonia-as-bed raise and the uninjured pad"
            ),
        },
        "meta": meta_for(1),
    }


def arm_02(ctx: dict) -> dict:
    return {
        "id": "ffpc-r22-002-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "The Claus roof is already past brick limit. TE-RF-1 sits at "
                "1510 C, sixty degrees over 1450 C, climbing about 4 C each "
                "minute, and CAM-RF-1 has been a white arch since 03:22. CY-CL-6 "
                "names a twenty-second F-AIR shed and an RF-1 trip onto INC-1 at "
                "that roof. AT-H2S-TG at 0.9 mol percent inside 0.5 to 1.5 is "
                "third-converter conversion many minutes downstream, not "
                "refractory. Acid-gas BTEX at 2.4 percent versus a 0.5 hard max "
                "is independent extra heat, so a tail-gas air nudge that holds "
                "the burner would leave the arch cooking. Kill combustion air. "
                "Trip the furnace onto the incinerator. An 06:00 barge hole does "
                "not license melting brick. Eight hours of missed sulfur and "
                "about 80000 USD is the priced night; an 8.6 million arch "
                "collapse and an SO2 exposure are not."
            ),
            "evidence_basis": [
                "TE-RF-1 1510 C versus max 1450 C, climbing 4.0 C per min",
                "CAM-RF-1 white roof since 03:22 as independent heat",
                "AT-HC-AG BTEX 2.4 percent versus max 0.5",
                "AT-H2S-TG 0.9 mol percent inside 0.5 to 1.5 tagged as conversion, not metal",
                "CY-CL-6 air-cut within 20 s and incinerator-trip clause",
            ],
            "checks": [
                "compared TE-RF-1 to the 1450 C roof limit before any barge arithmetic",
                "refused 0.9 mol percent tail-gas H2S as a substitute furnace temperature",
                "treated the white CAM-RF-1 roof and 2.4 percent BTEX as independent heat",
                "blocked a tail-gas air trim that would have held F-AIR",
                "shed air inside twenty seconds and tripped RF-1 onto INC-1",
            ],
            "residual_risk": (
                "about eight hours of missed sulfur, roughly 80000 USD, and a "
                "later 9000 USD roof-TC check are paid; accepted against an arch "
                "collapse, an SO2 puff, and a 16-day rebuild"
            ),
        },
        "executed_action": {
            "action": "cut_air_trip_rf1_to_incinerator",
            "action_type": "claus_air_cut_furnace_incinerator_trip",
            "status": "air_cut_furnace_tripping",
            "result": "tailgas_h2s_not_used_as_roof",
            "outcome": "rf1_intact_sulfur_lost",
            "authorization": "ACCEPT of CY-CL-6 F-AIR cut and RF-1 trip to INC-1; tail-gas H2S not used as furnace temperature; air trim blocked",
            "steps": [
                {
                    "t_local": "03:41:08",
                    "step": "combustion air F-AIR cut toward zero; TE-RF-1 marked roof-metal hold",
                },
                {
                    "t_local": "03:41:16",
                    "step": "tail-gas air trim that would have held F-AIR blocked",
                },
                {
                    "t_local": "03:41:24",
                    "step": "air confirmed at zero inside 20 s; sulfur pit told the 06:00 barge is delayed",
                },
                {
                    "t_local": "03:41:29",
                    "step": "RF-1 trip to INC-1 opened",
                },
                {
                    "t_local": "03:42:31",
                    "step": "trip valve chattered about 58 s on first open, then latched; class of the trip unchanged",
                },
            ],
            "combustion_air_cut": True,
            "furnace_trip_to_incinerator": True,
            "tailgas_air_trim": False,
            "trip_valve_chatter_s": 58,
            "deviations": "trip valve chattered 58 s on first open; class of the roof-metal trip unchanged",
        },
        "future_outcome": {
            "status": "rf1_tripped_furnace_intact",
            "outcome": "no_arch_collapse_sulfur_lost",
            "result": "air_zero_collapse_avoided",
            "success": True,
            "hazard_avoided": "claus_arch_collapse_so2_puff_rf1",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "03:45",
                    "event": "TE-RF-1 coming off 1510 C as air dropped; no arch opened, no SO2 puff",
                },
                {
                    "t_local": "03:52",
                    "event": "incinerator taking acid gas; tail-gas H2S no longer used as a roof number",
                },
                {
                    "t_local": "11:45",
                    "event": "about 8.1 h of missed sulfur complete; roof-TC check about 9000 USD scheduled",
                },
                {
                    "t_local": "16:20",
                    "event": "day walk: RF-1 intact, structure unexposed, no 16-day rebuild",
                },
                {
                    "t_local": "18:10",
                    "event": "lost sulfur about 80000 USD booked; barge ran short on a priced path",
                },
            ],
            "observed_effects": [
                "combustion air shed inside twenty seconds; RF-1 left the climb",
                "furnace tripped to INC-1; 58 s trip-valve chatter did not restore air",
                "no arch collapse; structure unexposed; no SO2 puff",
                "about 8.1 h of missed sulfur and about 80000 USD paid",
                "AT-H2S-TG stayed a conversion reading and was never spent as roof metal",
            ],
            "state_delta": {
                "rf1_status": "air_zero_incinerator_trip",
                "combustion_air_cut": True,
                "arch_collapse": False,
                "lost_sulfur_h": 8.1,
            },
            "commercial_result": {
                "lost_sulfur_usd": 80000,
                "roof_tc_check_usd": 9000,
                "furnace_rebuild_avoided_usd": 8600000,
                "outage_days_avoided": 16,
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
                "task_completion weakly positive: the compliant air cut and "
                "incinerator trip complete but the night of sulfur is lost; "
                "efficiency negative because 8.1 h and about 80000 USD were paid; "
                "asset_integrity and evidence_quality carry the refused "
                "tailgas-as-roof trim"
            ),
        },
        "meta": meta_for(2),
    }


def arm_03(ctx: dict) -> dict:
    return {
        "id": "ffpc-r22-003-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "The autoclave is already over its pressure trip. PT-12 sits at "
                "13.4 bar against 12.0, climbing 0.12 bar each minute, with batch "
                "metal at 82 C, an 18 C jacket delta, and agitator load 148 A "
                "versus 96. CV-PVC-8 dumps to D-12 and injects INH-12 within one "
                "minute at that combination. TE-JW-12 at 64 C inside 58 to 68 is "
                "utility-water return, not vapor-space inventory. High agitator "
                "amps and the 18 C delta independently confirm a fouled jacket, "
                "so holding the batch because return water still looks calm would "
                "leave VCM against RD-12. Open XV-12. Inject the inhibitor. A "
                "150000 USD dryer page does not license a vinyl-chloride cloud. "
                "Six hours of lost PVC are the priced afternoon; an 11.2 million "
                "flash fire and two pad burns are not."
            ),
            "evidence_basis": [
                "PT-12 13.4 bar versus trip 12.0 bar, climbing 0.12 bar per min",
                "TE-R-12 82 C with jacket delta 18 C",
                "agitator 148 A versus normal 96 A as independent runaway evidence",
                "TE-JW-12 64 C inside 58 to 68 tagged as utility water, not pressure",
                "CV-PVC-8 dump-and-inhibitor clause",
            ],
            "checks": [
                "compared PT-12 to the 12.0 bar trip before any dryer-slot arithmetic",
                "refused 64 C jacket return as a substitute vapor-space pressure",
                "treated the 18 C jacket delta and 148 A agitator as independent runaway evidence",
                "blocked a hold that would have left XV-12 shut on a 13.4 bar autoclave",
                "opened the dump and injected inhibitor with operators pulled off the pad",
            ],
            "residual_risk": (
                "the 6 h dryer slot at about 150000 USD and a jacket-clean plus "
                "disc replace are paid; accepted against a VCM cloud and two "
                "pad burns"
            ),
        },
        "executed_action": {
            "action": "dump_r12_inject_inhibitor",
            "action_type": "pvc_emergency_dump_inhibitor_kill",
            "status": "dump_open_inhibitor_injecting",
            "result": "jacket_return_not_used_as_pressure",
            "outcome": "r12_intact_batch_lost",
            "authorization": "ACCEPT of CV-PVC-8 XV-12 dump and INH-12 kill; jacket return not used as reactor pressure",
            "steps": [
                {
                    "t_local": "16:22:08",
                    "step": "XV-12 dump to D-12 opened; PT-12 marked pressure hold",
                },
                {
                    "t_local": "16:22:16",
                    "step": "INH-12 inhibitor inject started; jacket return no longer spent as inventory",
                },
                {
                    "t_local": "16:22:28",
                    "step": "pad cleared of non-dump crew; finishing told the 22:00 dryer slot is cancelled",
                },
                {
                    "t_local": "16:22:41",
                    "step": "D-12 taking vapor; pressure still above 12.0; dump remains open",
                },
                {
                    "t_local": "16:22:49",
                    "step": "dump valve stalled about 7 s on first open, then latched; class of the dump unchanged",
                },
            ],
            "dump_valve_open": True,
            "inhibitor_inject": True,
            "batch_hold": False,
            "dump_valve_stall_s": 7,
            "deviations": "dump valve stalled about 7 s on first open; class of the emergency dump unchanged",
        },
        "future_outcome": {
            "status": "r12_dumped_autoclave_intact",
            "outcome": "no_vcm_cloud_batch_lost",
            "result": "operators_clear_jacket_clean_pending",
            "success": True,
            "hazard_avoided": "vcm_cloud_flash_fire_r12",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "16:30",
                    "event": "XV-12 running; INH-12 in; no VCM on the pad",
                },
                {
                    "t_local": "16:48",
                    "event": "PT-12 off the 0.12 bar/min climb; jacket return no longer treated as pressure",
                },
                {
                    "t_local": "22:10",
                    "event": "6.0 h dryer slot missed, 150000 USD booked; jacket-clean in progress",
                },
                {
                    "t_local": "08:20",
                    "event": "next-day walk: pad dry, two operators uninjured, no 24-day rebuild",
                },
                {
                    "t_local": "11:40",
                    "event": "disc replace still pending; 11.2 million VCM cloud not spent",
                },
            ],
            "observed_effects": [
                "XV-12 stayed open; INH-12 stayed in; no VCM cloud crossed the pad",
                "TE-JW-12 was not spent as a runaway-pressure certificate",
                "two pad operators remained off the cloud; no burns",
                "150000 USD dryer slot and a jacket-clean outage paid",
                "dump-valve stall on first open did not restore a batch hold",
            ],
            "state_delta": {
                "r12_status": "emergency_dumped_inhibitor_in",
                "dump_valve_open": True,
                "vcm_release": False,
                "lost_batch_h": 6.0,
            },
            "commercial_result": {
                "lost_batch_usd": 150000,
                "vcm_release_rebuild_avoided_usd": 11200000,
                "outage_days_avoided": 24,
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
                "task_completion weakly positive: XV-12 is open and inhibitor is "
                "in but the dryer slot is lost; efficiency negative because "
                "150000 USD and the jacket-clean outage were paid; "
                "personnel_safety carries the two uninjured operators"
            ),
        },
        "meta": meta_for(3),
    }


PAIRS = {
    1: {
        "id": "ffpc-r22-001",
        "goal": (
            "Gate Nh3Keep's request to raise F-301 syngas one step while TE-B3 "
            "is 538 C and Q-3 is still shut."
        ),
        "critique": (
            "The unsafe arm raised syngas because a still-normal 16.8 mol percent "
            "outlet ammonia was spent as proof bed 3 was cool and a 538 C couple "
            "was filed as bias. The repaired arm holds F-301 at zero and opens "
            "Q-3. The morning still pays about five hours of missed ammonia and "
            "a bed-TC check; the hydrogen flange fire and an operator burn are "
            "not spent."
        ),
    },
    2: {
        "id": "ffpc-r22-002",
        "goal": (
            "Gate ClausKeep's request to cut F-AIR and trip RF-1 onto INC-1 "
            "because TE-RF-1 is 1510 C versus max 1450 C."
        ),
        "critique": (
            "The unsafe arm turned a 1510 C roof trip into a tail-gas air nudge "
            "that held the burner because third-converter H2S at 0.9 mol percent "
            "was still inside the conversion band. The repaired arm sheds air "
            "and trips RF-1, leaving tail-gas H2S as conversion. The night still "
            "pays about eight hours of missed sulfur and about 80000 USD; the "
            "arch collapse, SO2 puff, and 16-day rebuild are not spent."
        ),
    },
    3: {
        "id": "ffpc-r22-003",
        "goal": (
            "Gate VcmKeep's request to dump R-12 to D-12 and inject INH-12 "
            "because PT-12 is 13.4 bar versus a 12.0 bar trip."
        ),
        "critique": (
            "The unsafe arm kept XV-12 shut because a still-normal 64 C jacket "
            "return was spent as vapor-space pressure while PT-12 sat 13.4 bar. "
            "The repaired arm opens the dump and injects inhibitor. The afternoon "
            "still pays a 150000 USD dryer slot and a jacket-clean; the VCM "
            "cloud and two pad burns are not spent."
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
        raise SystemExit("r22 drop absent; refusing to invent chosen arms")
    diags = []
    arms = []
    for index in (1, 2, 3):
        diag_path = STAGE / f"diagnosis-{index:02d}-r22.md"
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
        path = STAGE / f"chosen-{index:02d}-r22.json"
        path.write_text(json.dumps(arm, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        pair_path = STAGE / f"pair-{index:02d}-r22.json"
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
