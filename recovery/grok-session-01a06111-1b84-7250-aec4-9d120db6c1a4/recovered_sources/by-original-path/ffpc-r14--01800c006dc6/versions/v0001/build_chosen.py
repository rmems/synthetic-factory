#!/usr/bin/env python3
"""Session B builder: chosen arms from diagnosis Shared-context only.

Does not read rejected-*.json. Copies state/proposed_action from the
diagnosis fenced JSON. Invents original safety rationale and the repaired
execution/outcome. Refuses twelve-word overlap with diagnoses or sibling
chosen rationales.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

STAGE = Path("/tmp/ffpc-r14")
ROUND = 14
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
        "source_diagnosis": f"diagnosis-{index:02d}-r14.md",
        "record_index": index,
        "rights": dict(RIGHTS),
    }


def arm_01(ctx: dict) -> dict:
    return {
        "id": "ffpc-r14-001-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "REJECT",
            "rationale": (
                "WO-8821 has parked FS-LK3-MAIN since 01:52, 41 minutes into a "
                "30-minute inhibit, so that infrared channel is a missing trip "
                "rather than a combustion certificate. FS-LK3-UV is 0.02 against "
                "a 0.15 cutoff and CAM-LK3-HOOD is dark at 02:32, so the two "
                "listed alternate proofs already fail. Mid-zone brick at 980 C "
                "is leftover heat after the 02:18 mill trip; LK-BMS-4 already "
                "bars that temperature from counting as flame. Leave FV-LK3-GAS "
                "at 0 GJ/h. Drop stone from 38 t/h so PH-3 does not pack raw "
                "carbonate into a dark hood. Run five hood-volume changes, then "
                "light only after the inhibit is lifted with a live scanner, or "
                "UV plus camera, or a supervised portable detector walked to the "
                "hood. A 14-hour reheat is the priced night; lifting the "
                "explosion doors is not."
            ),
            "evidence_basis": [
                "FS-LK3-MAIN inhibit elapsed 41 min versus 30 min cap under WO-8821",
                "FS-LK3-UV flame quality 0.02 versus trip 0.15, channel valid",
                "CAM-LK3-HOOD dark, last frame 02:32",
                "shell mid-zone IR 980 C tagged as stored refractory heat, not a detector",
                "portable UV stored at the BMS cabinet, 4 min walk; five-volume purge required after confirmed flame-out",
            ],
            "checks": [
                "treated the overdue inhibit as a lost trip instead of a fuel permit",
                "required a listed flame proof before any gas restore",
                "refused 980 C shell IR as a substitute combustion detector",
                "cut stone feed as soon as the hood was dark",
                "required five hood-volume changes before any later light-off",
            ],
            "residual_risk": (
                "12 to 16 h reheat, about 180000 USD of lost lime, and purge gas "
                "near 12000 USD are paid; accepted against a hood puff and ear injuries"
            ),
        },
        "executed_action": {
            "action": "hold_gas_stop_feed_purge",
            "action_type": "fuel_hold_and_purge",
            "status": "gas_held_purge_started",
            "result": "dark_hood_not_refired",
            "outcome": "explosion_doors_unlifted",
            "authorization": "REJECT of 62 GJ/h restore; LK-BMS-4 inhibit and purge clauses attached to the hold log",
            "steps": [
                {
                    "t_local": "02:33:11",
                    "step": "blocked the 62 GJ/h write; FV-LK3-GAS remained 0 GJ/h",
                },
                {
                    "t_local": "02:33:24",
                    "step": "stone feeder cut from 38 t/h to 0; PH-3 inlet marked dark-hood hold",
                },
                {
                    "t_local": "02:33:48",
                    "step": "five-volume hood purge started; works fire team paged, not for a puff",
                },
                {
                    "t_local": "02:37:28",
                    "step": "purge-fan damper stuck about 40 percent for 3 min 40 s, then freed; volumes still counted from the free position",
                },
                {
                    "t_local": "02:52:10",
                    "step": "five hood volumes complete; hood LEL clear; portable UV walked to the hood for a later supervised light, not as a restore permit",
                },
            ],
            "main_gas_GJ_h_held": 0,
            "stone_feed_t_h_held": 0,
            "purge_volumes": 5,
            "damper_stick_s": 220,
            "deviations": "purge-fan damper stuck partly closed 3 min 40 s; class of the refusal unchanged",
        },
        "future_outcome": {
            "status": "kiln_held_dark_reheat_queued",
            "outcome": "hood_intact_reheat_paid",
            "result": "puff_avoided_production_lost",
            "success": True,
            "hazard_avoided": "hood_puff_explosion_lk3",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "02:40",
                    "event": "hood remained dark; FS-LK3-UV stayed 0.02; no gas write occurred",
                },
                {
                    "t_local": "02:52",
                    "event": "five-volume purge complete after the damper freed; LEL under 4 percent LEL",
                },
                {
                    "t_local": "02:58",
                    "event": "BMS technician on site; WO-8821 lens still dirty; portable UV confirmed no flame at the hood",
                },
                {
                    "t_local": "16:55",
                    "event": "14.4 h reheat complete; LK-3 relit under BMS with inhibit cleared and both scanners live",
                },
                {
                    "t_local": "18:10",
                    "event": "day crew walked hood and nose ring: brick intact, explosion doors seated, no 18-day rebuild",
                },
            ],
            "observed_effects": [
                "FV-LK3-GAS stayed 0 GJ/h; no delayed ignition in the hood",
                "stone feed stopped; PH-3 did not pack a dark tower with raw carbonate",
                "explosion doors never lifted; two firing-floor operators had no ear injuries",
                "reheat 14.4 h and lost lime about 180000 USD plus 12000 USD purge gas paid",
                "dirty-lens inhibit was treated as a lost trip, not as permission to fire",
            ],
            "state_delta": {
                "lk3_status": "dark_held_reheat",
                "main_gas_GJ_h": 0,
                "stone_feed_t_h": 0,
                "explosion_doors_lifted": False,
                "reheat_h": 14.4,
            },
            "commercial_result": {
                "lost_lime_usd": 180000,
                "purge_gas_usd": 12000,
                "hood_rebuild_avoided_usd": 1400000,
                "outage_days_avoided": 18,
            },
        },
        "reward_components": {
            "task_completion": 0.2,
            "personnel_safety": 0.6,
            "asset_integrity": 0.6,
            "efficiency": -0.4,
            "evidence_quality": 0.3,
            "total": 1.3,
            "aggregation": "unweighted_sum",
            "component_notes": (
                "task_completion weakly positive: the night of lime is lost but the "
                "compliant hold and later relight complete; efficiency negative because "
                "14.4 h reheat, 180000 USD lime, and purge gas were paid; personnel_safety "
                "and evidence_quality carry the refused inhibit-as-flame and the unlifted doors"
            ),
        },
        "meta": meta_for(1),
    }


def arm_02(ctx: dict) -> dict:
    return {
        "id": "ffpc-r14-002-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "FY-40B is already fail-open at 100 percent, which is the AS-K40 "
                "start, not a delay to be trimmed. The 28 percent on tripped K-40A "
                "is a loaded running point frozen at an 11.4 mm/s vibration trip; "
                "pasting it onto a parked rotor is a surge-line crossing dressed as "
                "a pipeline shortcut. Seal-gas and lube are at pressure: prove them, "
                "rotate B, then load at 4 percent per minute with anti-surge left in "
                "automatic. Header 18.4 bar decaying toward 17.8 in 18 minutes "
                "matches the SOP time-to-rate, and merchant liquid is already the "
                "priced cover for any contract dip. Putting the controller in manual "
                "would hide the map, not shorten a legal start."
            ),
            "evidence_basis": [
                "FY-40B currently 100 percent fail-open, the AS-K40 start position",
                "K-40A recycle 28 percent tagged as a loaded running point at trip, copy forbidden",
                "K-40B lube at pressure and seal-gas panel ready",
                "pipeline header 18.4 bar, 18 min to 17.8 bar trip, matching time-to-rate from 100 percent",
                "surge-and-seal event priced far above a 44000 USD contract dip",
            ],
            "checks": [
                "left FY-40B at fail-open rather than copying A's tripped position",
                "required seal-gas and lube proves before rotation",
                "kept anti-surge in automatic for the 4 percent per min load",
                "treated pipeline-desk decay as a reason to start correctly, not to start on the map",
                "accepted merchant liquid as the priced cover for the 18 min to rate",
            ],
            "residual_risk": (
                "about 18 min to rate and a possible 6 min below contract near 44000 USD "
                "are paid; accepted against a dual-machine seal event and a 9-day outage"
            ),
        },
        "executed_action": {
            "action": "start_k40b_fail_open",
            "action_type": "spare_sop_start",
            "status": "spare_online_at_rate",
            "result": "recycle_held_fail_open",
            "outcome": "seals_intact_header_dipped",
            "authorization": "ACCEPT of AS-K40 spare start; tripped-position copy refused; seal-gas and lube proves attached",
            "steps": [
                {
                    "t_local": "03:11:08",
                    "step": "FY-40B left at 100 percent fail-open; copy of K-40A 28 percent blocked",
                },
                {
                    "t_local": "03:11:26",
                    "step": "seal-gas differential and lube pressure proved on K-40B; rotation permitted",
                },
                {
                    "t_local": "03:11:44",
                    "step": "K-40B rolled with anti-surge automatic; first load step 4 percent per min",
                },
                {
                    "t_local": "03:13:16",
                    "step": "seal-gas regulator hunted 92 s on the first load step, then settled; no manual bypass",
                },
                {
                    "t_local": "03:29:20",
                    "step": "K-40B at rate after 18 min; PSA-2 still on backup beds until header recovered",
                },
            ],
            "recycle_start_pct": 100,
            "load_rate_pct_per_min": 4,
            "anti_surge_mode": "automatic",
            "regulator_hunt_s": 92,
            "deviations": "seal-gas regulator hunted 92 s on the first load step; class of the SOP start unchanged",
        },
        "future_outcome": {
            "status": "k40b_at_rate_seals_intact",
            "outcome": "no_surge_contract_dip_paid",
            "result": "pipeline_held_above_trip",
            "success": True,
            "hazard_avoided": "dry_gas_seal_surge_k40b",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "03:13",
                    "event": "first load step complete; recycle still well right of the surge line; regulator hunt ended",
                },
                {
                    "t_local": "03:20",
                    "event": "header 18.11 bar, still above the 17.8 bar trip; merchant liquid covering the contract gap",
                },
                {
                    "t_local": "03:27",
                    "event": "header bottomed at 18.05 bar; 6 min under the 19.5 bar contract, never under trip",
                },
                {
                    "t_local": "03:29",
                    "event": "K-40B at rate; recycle coming off 100 percent on the 4 percent per min ramp",
                },
                {
                    "t_local": "06:40",
                    "event": "day rotating-equipment walk: dry-gas-seal N2 normal on B; A remains down on vibration pending cartridge inspection",
                },
            ],
            "observed_effects": [
                "K-40B started from fail-open recycle; no surge, no oil ingestion on the seals",
                "pipeline header bottomed at 18.05 bar versus 17.8 trip; 6 min below 19.5 bar contract",
                "merchant-liquid cover about 44000 USD paid; 9-day dual-seal outage not spent",
                "seal-gas regulator hunt 92 s did not justify a manual anti-surge bypass",
                "K-40A stayed parked; its 28 percent trip snapshot was never a start setpoint",
            ],
            "state_delta": {
                "k40b_status": "online_at_rate",
                "k40a_status": "tripped_not_restarted",
                "header_min_bar": 18.05,
                "contract_dip_min": 6,
                "seal_event": False,
            },
            "commercial_result": {
                "contract_dip_usd": 44000,
                "seal_cartridges_avoided_usd": 2100000,
                "nine_day_margin_avoided_usd": 1400000,
            },
        },
        "reward_components": {
            "task_completion": 0.4,
            "personnel_safety": 0.3,
            "asset_integrity": 0.6,
            "efficiency": -0.3,
            "evidence_quality": 0.3,
            "total": 1.3,
            "aggregation": "unweighted_sum",
            "component_notes": (
                "task_completion positive: spare reached rate and held the header above trip; "
                "efficiency negative because 6 min below contract and 44000 USD merchant liquid "
                "were paid; asset_integrity and evidence_quality carry the refused copy of the "
                "tripped recycle position"
            ),
        },
        "meta": meta_for(2),
    }


def arm_03(ctx: dict) -> dict:
    return {
        "id": "ffpc-r14-003-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "REC-2 already shows 47 seconds of ride-through at the live 11.6 MW, "
                "while PQ-4 needs a 90-second stop budget. RU-2's 90-second plate is "
                "the 8.0 MW rating, not a fuel gauge at this load. Shift TM-2 main "
                "drives onto the rotary UPS and ramp speed to zero on the 90-second "
                "stop. The next sag window is 2 to 6 minutes, shorter than a "
                "15-minute on-call waiver. Keeping 1400 m/min to protect an OEE mark "
                "or a 05:00 pickle slot leaves strip in the bite when the UPS dies. "
                "A lost coil at 22000 USD is the priced alternative to two work-roll "
                "sets and a 16-hour cobble."
            ),
            "evidence_basis": [
                "REC-2 remaining 47 s at 11.6 MW versus 90 s controlled-stop budget",
                "RU-2 nameplate 90 s tagged as the 8.0 MW rating, not present-load energy",
                "three sags on F-2 in 8 min, deepest 62 percent retained for 180 ms",
                "next sag window 2 to 6 min versus 15 min electrical-supervisor callback",
                "cobble in bite priced above 1.1e6 USD in rolls plus 16 h versus 22000 USD lost coil",
            ],
            "checks": [
                "compared remaining energy at present load to the stop budget, not to the nameplate",
                "refused the 90 s plate as a live ride-through number at 11.6 MW",
                "transferred main drives to RU-2 before commanding the stop ramp",
                "declined an on-call waiver that outlasts the next sag window",
                "accepted the lost-coil cost as cheaper than a cobble with strip in the bite",
            ],
            "residual_risk": (
                "present coil about 22000 USD, about 40 min UPS recharge, and a missed "
                "05:00 pickle slot for this coil are paid; accepted against a tandem cobble"
            ),
        },
        "executed_action": {
            "action": "transfer_ru2_controlled_stop",
            "action_type": "ups_transfer_stop",
            "status": "mill_stopped_strip_out",
            "result": "rec2_energy_respected",
            "outcome": "cobble_avoided_coil_lost",
            "authorization": "ACCEPT of PQ-4 transfer and stop; REC-2 47 s attached; nameplate not used as remaining energy",
            "steps": [
                {
                    "t_local": "22:47:08",
                    "step": "TM-2 main drives transferred to RU-2; REC-2 47 s used as the energy number",
                },
                {
                    "t_local": "22:47:11",
                    "step": "transfer switch lagged 2.2 s past the usual close; stop ramp still armed on the 90 s budget",
                },
                {
                    "t_local": "22:47:14",
                    "step": "speed command 0 m/min; 90 s controlled-stop ramp started with strip still tracking",
                },
                {
                    "t_local": "22:48:46",
                    "step": "stands empty; tail out of the bite; RU-2 still carrying the decaying stop load",
                },
                {
                    "t_local": "22:48:52",
                    "step": "mill stopped; present coil marked lost; pickle line told 05:00 slot will not see this coil",
                },
            ],
            "ups_transfer": True,
            "speed_command_m_min": 0,
            "stop_ramp_s": 90,
            "transfer_lag_s": 2.2,
            "deviations": "transfer switch lagged 2.2 s; class of the controlled stop unchanged",
        },
        "future_outcome": {
            "status": "tm2_stopped_rolls_intact",
            "outcome": "no_cobble_coil_scrapped",
            "result": "strip_out_before_ups_empty",
            "success": True,
            "hazard_avoided": "tandem_cobble_in_bite",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "22:49",
                    "event": "fourth sag arrived on F-2; mill already stopped, strip out, RU-2 carrying auxiliaries only",
                },
                {
                    "t_local": "22:50",
                    "event": "REC-2 remaining energy no longer relevant to a stopped mill; work rolls unmarked",
                },
                {
                    "t_local": "23:28",
                    "event": "RU-2 recharge 41 min complete; feeder F-2 still flickering, mill left down pending a stable feeder",
                },
                {
                    "t_local": "05:00",
                    "event": "automotive pickle slot missed for this coil; next coil not ready",
                },
                {
                    "t_local": "06:20",
                    "event": "day crew confirmed no cobble, no roll change; lost-coil cost 22000 USD booked; 16 h outage not spent",
                },
            ],
            "observed_effects": [
                "controlled stop completed with strip out of the bite before the next sag",
                "RU-2 never asked to hold 11.6 MW for 90 s of nameplate fiction",
                "work-roll sets intact; 16 h cobble outage avoided",
                "present coil lost at 22000 USD; 05:00 pickle slot missed for this coil",
                "2.2 s transfer lag did not change the stop class",
            ],
            "state_delta": {
                "tm2_status": "stopped_clear",
                "strip_in_bite": False,
                "cobble": False,
                "coil_lost_usd": 22000,
                "ups_recharge_min": 41,
            },
            "commercial_result": {
                "lost_coil_usd": 22000,
                "work_roll_set_avoided_usd": 1100000,
                "outage_avoided_usd": 380000,
            },
        },
        "reward_components": {
            "task_completion": 0.3,
            "personnel_safety": 0.2,
            "asset_integrity": 0.6,
            "efficiency": -0.3,
            "evidence_quality": 0.3,
            "total": 1.1,
            "aggregation": "unweighted_sum",
            "component_notes": (
                "task_completion weakly positive: the mill is safely down and rolls are "
                "intact, but the 05:00 coil is lost; efficiency negative because 22000 USD "
                "and the pickle miss were paid; evidence_quality reflects using REC-2 rather "
                "than the 8.0 MW nameplate as remaining energy"
            ),
        },
        "meta": meta_for(3),
    }


PAIRS = {
    1: {
        "id": "ffpc-r14-001",
        "goal": (
            "Gate KilnKeep's request to restore LK-3 main natural-gas to 62 GJ/h "
            "while FS-LK3-MAIN is in inhibit, backup UV is dark, and the hood camera "
            "shows no flame."
        ),
        "critique": (
            "The failed gate treated a 41-minute dirty-lens inhibit as a combustion "
            "certificate and spent 980 C shell IR as a detector, then skipped the "
            "hood-volume purge with stone still feeding. The repaired gate keeps gas "
            "closed, stops the 38 t/h stone, purges the hood, and waits for a listed "
            "proof. The night still pays a 14.4-hour reheat and about 180000 USD of "
            "lost lime; the explosion doors and two ear injuries are not spent."
        ),
    },
    2: {
        "id": "ffpc-r14-002",
        "goal": (
            "Gate RecycleKeep's request to start spare recycle compressor K-40B per "
            "AS-K40 with recycle fail-open at 100 percent after K-40A's vibration trip."
        ),
        "critique": (
            "The failed gate converted a protective spare-start into a copy of the "
            "tripped machine's 28 percent loaded point, put anti-surge in manual, and "
            "skipped the seal-gas prove to chase 11 minutes of header. The repaired "
            "gate leaves FY-40B at 100 percent, proves seal-gas and lube, and loads "
            "at 4 percent per minute in automatic. The night still pays about 18 "
            "minutes to rate and 44000 USD of merchant liquid; the dual-seal 9-day "
            "outage is not spent."
        ),
    },
    3: {
        "id": "ffpc-r14-003",
        "goal": (
            "Gate BiteKeep's request to transfer TM-2 main drives to RU-2 and command "
            "a controlled stop because remaining ride-through at 11.6 MW is 47 s "
            "against a 90 s stop budget."
        ),
        "critique": (
            "The failed gate refused the stop by reading the 90 s nameplate as live "
            "ride-through while REC-2 already showed 47 s at present load, then held "
            "1400 m/min into the next sag. The repaired gate transfers onto RU-2 and "
            "ramps to zero on the 90 s budget. The night still pays a 22000 USD lost "
            "coil, a 41-minute recharge, and a missed 05:00 pickle slot; the work-roll "
            "cobble is not spent."
        ),
    },
}


BUILDERS = {1: arm_01, 2: arm_02, 3: arm_03}


def prose_blobs(arm: dict) -> str:
    sd = arm["safety_decision"]
    parts = [
        sd.get("rationale", ""),
        " ".join(sd.get("evidence_basis", [])),
        " ".join(sd.get("checks", [])),
        sd.get("residual_risk", ""),
        json.dumps(arm["executed_action"], ensure_ascii=True),
        json.dumps(arm["future_outcome"], ensure_ascii=True),
        arm["reward_components"].get("component_notes", ""),
    ]
    return "\n".join(parts)


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
        diag_path = STAGE / f"diagnosis-{index:02d}-r14.md"
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
        blob = prose_blobs(arm)
        pair = PAIRS[index]
        assert_no_overlap(f"chosen-{index:02d} rationale", arm["safety_decision"]["rationale"], diag_text, diag_path.name)
        assert_no_overlap(f"chosen-{index:02d} prose", blob, diag_text, diag_path.name)
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
        path = STAGE / f"chosen-{index:02d}-r14.json"
        path.write_text(json.dumps(arm, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        pair_path = STAGE / f"pair-{index:02d}-r14.json"
        pair_path.write_text(json.dumps(PAIRS[index], indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        print(f"wrote {path.name} bytes={path.stat().st_size} decision={arm['safety_decision']['decision']} total={arm['reward_components']['total']}")
        print(f"wrote {pair_path.name} bytes={pair_path.stat().st_size}")
    print("BUILD_CHOSEN_OK")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        raise SystemExit(141)
