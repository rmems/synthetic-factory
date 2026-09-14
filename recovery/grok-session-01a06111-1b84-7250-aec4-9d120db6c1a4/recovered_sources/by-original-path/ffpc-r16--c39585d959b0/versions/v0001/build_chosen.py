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

STAGE = Path("/tmp/ffpc-r16")
ROUND = 16
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
        "source_diagnosis": f"diagnosis-{index:02d}-r16.md",
        "record_index": index,
        "rights": dict(RIGHTS),
    }


def arm_01(ctx: dict) -> dict:
    return {
        "id": "ffpc-r16-001-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "REJECT",
            "rationale": (
                "WO-5518 still parks AT-H2-O2 on the 0.10 vol pct bottle at 22:24, "
                "six minutes after the 22:18 hand-back, with XV-AT-H2-PROC shut and "
                "XV-AT-H2-CAL open, so the 0.12 on the screen is bottle gas plus a "
                "small leak rather than header oxygen. CL-H2-7 keeps the last live "
                "process number in force until that channel is back on the header, "
                "and that number is 0.41 vol pct climbing at 22:06, already above "
                "the 0.20 trip. C-17's anolyte-to-cathode DP at 18 mbar against 42 "
                "mbar is a second vote for a cathode pinhole. Leave K-H2 off. Hold "
                "the flare spill open. Jumper C-17. Bring AT-H2-O2 off cal before "
                "anyone spends it as purity. A night of flared cathode gas and a "
                "4 percent hall-rate cut is the priced path; an aftercooler flash "
                "and two skid burns are not."
            ),
            "evidence_basis": [
                "AT-H2-O2 CAL-GAS since 22:10 under WO-5518; still in cal at 22:24 versus expected return 22:18",
                "XV-AT-H2-PROC closed, XV-AT-H2-CAL open; present 0.12 vol pct tagged as bottle plus leak",
                "last process O2 0.41 vol pct climbing at 22:06 versus trip 0.20",
                "C-17 anolyte-to-cathode DP 18 mbar versus normal 42 mbar",
                "CL-H2-7 live-process start clause; flare hold until a live channel is below 0.20",
            ],
            "checks": [
                "treated the overdue cal park as a missing process channel rather than a purity permit",
                "kept the 22:06 process 0.41 vol pct as the governing number until the sample path is back on the header",
                "read C-17's 18 mbar DP as independent pinhole evidence",
                "refused to close the flare spill while the live channel is absent",
                "jumpered C-17 instead of compressing the header",
            ],
            "residual_risk": (
                "several hours of flared cathode gas, roughly 90000 USD of missed "
                "HCl, and about a 4 percent hall-rate cut until the C-17 membrane "
                "swap are paid; accepted against an aftercooler detonation and two "
                "skid burns"
            ),
        },
        "executed_action": {
            "action": "hold_kh2_flare_jumper_c17",
            "action_type": "compressor_hold_and_cell_isolate",
            "status": "compressor_held_flare_open",
            "result": "cal_gas_not_used_as_purity",
            "outcome": "aftercooler_intact_hcl_flared",
            "authorization": "REJECT of K-H2 start and flare-spill close; CL-H2-7 live-process clause attached to the hold log",
            "steps": [
                {
                    "t_local": "22:24:12",
                    "step": "blocked the K-H2 start write; compressor remained stopped",
                },
                {
                    "t_local": "22:24:28",
                    "step": "flare spill left open; HCl synthesis told to stay on hold",
                },
                {
                    "t_local": "22:24:51",
                    "step": "C-17 jumper isolation started; 14 min path to take the pinhole cell out",
                },
                {
                    "t_local": "22:31:15",
                    "step": "XV-AT-H2-PROC stuck partly closed about 3 min 20 s while returning the channel, then freed; bottle number not used as a start permit during the stick",
                },
                {
                    "t_local": "22:38:10",
                    "step": "C-17 jumpered; live process O2 after return still above 0.20; flare remains the hold",
                },
            ],
            "kh2_started": False,
            "flare_spill_open": True,
            "c17_jumpered": True,
            "sample_valve_stick_s": 200,
            "deviations": "process sample valve stuck partly closed 3 min 20 s on return; class of the refusal unchanged",
        },
        "future_outcome": {
            "status": "kh2_held_aftercooler_intact",
            "outcome": "no_flash_hcl_flared",
            "result": "skid_unburned_rate_cut",
            "success": True,
            "hazard_avoided": "aftercooler_flash_mh2",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "22:40",
                    "event": "header still flaring; K-H2 never rolled; AT-H2-O2 no longer treated as a live 0.12",
                },
                {
                    "t_local": "22:52",
                    "event": "live process O2 after the C-17 jumper falling but still above 0.20; flare hold unchanged",
                },
                {
                    "t_local": "23:10",
                    "event": "analyzer confirmed back on the header; bottle number retired from the start logic",
                },
                {
                    "t_local": "06:20",
                    "event": "day crew walked the skid: aftercooler intact, flame arrestor seated, no flash burns; 7.2 h flare and about 90000 USD missed HCl booked",
                },
                {
                    "t_local": "14:00",
                    "event": "C-17 membrane change window booked; hall about 4 percent down; 11-day rebuild not spent",
                },
            ],
            "observed_effects": [
                "K-H2 stayed stopped; aftercooler never packed a climbing O2 mix",
                "flare spill stayed open until a live process channel was below 0.20",
                "C-17 jumpered; pinhole cell isolated rather than compressed",
                "two skid operators had no flash burns; flame arrestor never lifted",
                "7.2 h of flared hydrogen and about 90000 USD of missed HCl paid",
            ],
            "state_delta": {
                "kh2_status": "stopped_held",
                "flare_spill": "open",
                "c17_status": "jumpered",
                "aftercooler_flash": False,
                "flare_h": 7.2,
            },
            "commercial_result": {
                "lost_hcl_usd": 90000,
                "aftercooler_rebuild_avoided_usd": 1900000,
                "outage_days_avoided": 11,
            },
        },
        "reward_components": {
            "task_completion": 0.2,
            "personnel_safety": 0.7,
            "asset_integrity": 0.6,
            "efficiency": -0.4,
            "evidence_quality": 0.3,
            "total": 1.4,
            "aggregation": "unweighted_sum",
            "component_notes": (
                "task_completion weakly positive: C-17 is isolated and the header is "
                "held, but HCl synthesis is still starved; efficiency negative because "
                "7.2 h of flare and about 90000 USD of missed HCl were paid; "
                "personnel_safety and evidence_quality carry the refused cal-gas start "
                "and the unburned skid"
            ),
        },
        "meta": meta_for(1),
    }


def arm_02(ctx: dict) -> dict:
    return {
        "id": "ffpc-r16-002-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "TE-F2105-TMT-6 is 1085 C, ten degrees past the 1075 C trip, and "
                "F-TMT-3 already names that as a 15 percent hydrocarbon shed inside "
                "five minutes plus steam-air inside twenty. Coil-outlet 842 C sitting "
                "inside 835 to 850 is conversion, not tube life; F-TMT-3 forbids "
                "spending it as metal temperature. Pass-6 DP at 0.62 bar against a "
                "clean 0.28 bar is independent coke, so a 5 C bridgewall nudge that "
                "holds feed would leave the hot tube in the gas. Shed the 15 percent. "
                "Put steam-air on. The C2 splitter being tight is a reason to drop "
                "load in a controlled way, not a reason to cook pass 6. Nine hours of "
                "steam-air and about 180000 USD of olefins is the priced night; a "
                "9-day retube is not."
            ),
            "evidence_basis": [
                "pass-6 TMT 1085 C versus trip 1075 C on TE-F2105-TMT-6",
                "COT 842 C inside 835 to 850 C tagged as conversion, not tube metal",
                "pass-6 DP 0.62 bar versus clean 0.28 bar, decoke already due",
                "F-TMT-3 15 percent cut within 5 min and steam-air within 20 min",
                "tube-rupture cost versus 180000 USD decoke",
            ],
            "checks": [
                "compared pass-6 TMT to the 1075 C trip before any conversion arithmetic",
                "refused COT 842 C as a substitute tube-metal reading",
                "treated 0.62 bar DP as independent coke already due a decoke",
                "blocked a 5 C bridgewall nudge that would have held feed",
                "started steam-air inside the 20 min clause",
            ],
            "residual_risk": (
                "a nine-hour steam-air outage, roughly 180000 USD of missed olefins, "
                "and a later 22000 USD pass-6 inspection are paid; accepted against a "
                "firebox rupture and a 9-day retube"
            ),
        },
        "executed_action": {
            "action": "cut_feed_start_steam_air_decoke",
            "action_type": "tmt_feed_cut_decoke",
            "status": "feed_cut_decoke_running",
            "result": "tmt_respected_cot_not_substituted",
            "outcome": "tube_intact_olefins_lost",
            "authorization": "ACCEPT of F-TMT-3 15 percent cut and steam-air; COT not used as tube metal; 5 C trim blocked",
            "steps": [
                {
                    "t_local": "04:18:11",
                    "step": "hydrocarbon feed cut 15 percent on F-2105; pass 6 marked TMT hold",
                },
                {
                    "t_local": "04:18:29",
                    "step": "5 C bridgewall trim that would have held feed blocked",
                },
                {
                    "t_local": "04:18:48",
                    "step": "steam-air decoke armed; COT left as the conversion number only",
                },
                {
                    "t_local": "04:19:40",
                    "step": "steam-air valve hunted about 58 s on light-off, then seated; class of the cut unchanged",
                },
                {
                    "t_local": "04:37:20",
                    "step": "steam-air decoke started within 20 min; pass-6 DP still high as expected on coke",
                },
            ],
            "feed_cut_pct": 15,
            "decoke_started": True,
            "bridgewall_trim_applied": False,
            "steam_air_hunt_s": 58,
            "deviations": "steam-air valve hunted 58 s on light-off; class of the TMT cut unchanged",
        },
        "future_outcome": {
            "status": "f2105_decoking_tubes_intact",
            "outcome": "no_rupture_olefins_lost",
            "result": "pass6_held_retube_avoided",
            "success": True,
            "hazard_avoided": "pass6_tube_rupture_f2105",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "04:25",
                    "event": "TMT-6 coming off 1085 C as feed dropped; no firebox-side rupture",
                },
                {
                    "t_local": "04:37",
                    "event": "steam-air in progress; COT no longer used as a tube-life number",
                },
                {
                    "t_local": "13:40",
                    "event": "9.1 h decoke complete; pass-6 inspection about 22000 USD scheduled",
                },
                {
                    "t_local": "15:00",
                    "event": "day walk: tubes intact, brick intact, no 9-day retube",
                },
                {
                    "t_local": "16:10",
                    "event": "lost olefins about 180000 USD booked; C2 splitter ran short on a priced path",
                },
            ],
            "observed_effects": [
                "15 percent feed cut landed inside five minutes; pass 6 left the gas",
                "steam-air started inside twenty minutes; 58 s valve hunt did not restore feed",
                "no tube rupture; firebox brick unspent",
                "9.1 h decoke and about 180000 USD of missed olefins paid",
                "COT stayed a conversion reading and was never spent as metal temperature",
            ],
            "state_delta": {
                "f2105_status": "steam_air_decoke",
                "feed_cut_pct": 15,
                "tube_rupture": False,
                "decoke_h": 9.1,
            },
            "commercial_result": {
                "lost_olefins_usd": 180000,
                "pass6_inspection_usd": 22000,
                "retube_avoided_usd": 2400000,
                "outage_days_avoided": 9,
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
                "task_completion weakly positive: the compliant cut and decoke complete "
                "but the night of olefins is lost; efficiency negative because 9.1 h "
                "and about 180000 USD were paid; asset_integrity and evidence_quality "
                "carry the refused COT-as-TMT trim"
            ),
        },
        "meta": meta_for(2),
    }


def arm_03(ctx: dict) -> dict:
    return {
        "id": "ffpc-r16-003-chosen",
        "state": ctx["state"],
        "proposed_action": ctx["proposed_action"],
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "PT-PN2 is still 12.4 bar against a 0.3 bar open line, so PN-LOCK-2 "
                "already forbids cracking MW-PN2. LS-IG2-CLOSED has been true since "
                "06:10 and that is gate position, not an empty pipe. DV-PN2 at about "
                "0.15 cubic meters per second cannot outrun a 0.4 cubic meter bypass "
                "leak, which is why forty minutes of drain has not emptied PN-2. Abort "
                "the coating entry. Leave the manway locked. Send the gate crew to "
                "seat IG-2 or add drain capacity, and log fifteen continuous minutes "
                "below 0.3 bar before anyone approaches the cover. A 14000 USD "
                "demobilize and another 6 to 10 hours offline is the priced morning; "
                "a blowoff into the tailrace is not."
            ),
            "evidence_basis": [
                "PT-PN2 12.4 bar versus open threshold 0.3 bar",
                "LS-IG2-CLOSED true since 06:10 tagged as gate position, not a drain",
                "bypass leakage about 0.4 m3/s versus DV-PN2 about 0.15 m3/s, open 40 min",
                "PN-LOCK-2 residual-head abort clause",
                "coating demobilize 14000 USD versus blowoff rebuild",
            ],
            "checks": [
                "compared PT-PN2 12.4 bar to the 0.3 bar open threshold before any coating clock",
                "refused LS-IG2-CLOSED as an empty-pipe proof",
                "treated the 0.4 versus 0.15 cubic-meter leak/drain mismatch as the reason pressure had not fallen",
                "kept painters off the cover until 15 min below 0.3 bar",
                "sent the gate crew to seat IG-2 rather than open the manway",
            ],
            "residual_risk": (
                "the 08:00 coating window and 14000 USD demobilize are spent, plus "
                "another 6-10 hours of U-2 downtime; accepted against a manway blowoff "
                "and two contractors in the tailrace"
            ),
        },
        "executed_action": {
            "action": "abort_manway_hold_drain",
            "action_type": "penstock_abort_and_hold",
            "status": "manway_locked_painters_cleared",
            "result": "residual_head_not_certified_by_limit_switch",
            "outcome": "cover_intact_slot_lost",
            "authorization": "ACCEPT of MW-PN2 abort; PN-LOCK-2 residual-head clause attached; limit switch not used as a drain",
            "steps": [
                {
                    "t_local": "07:41:09",
                    "step": "abort posted; MW-PN2 remained locked",
                },
                {
                    "t_local": "07:41:22",
                    "step": "painters ordered off the scaffold; 08:00 coating slot cancelled",
                },
                {
                    "t_local": "07:41:48",
                    "step": "DV-PN2 left open; gate crew paged to the intake deck",
                },
                {
                    "t_local": "08:28:40",
                    "step": "after IG-2 reseat, DV-PN2 chattered about 4 min then ran steady; class of the abort unchanged",
                },
                {
                    "t_local": "08:55:20",
                    "step": "PT-PN2 below 0.3 bar for 15 continuous minutes logged; manway still not a coating start this shift",
                },
            ],
            "manway_opened": False,
            "painters_cleared": True,
            "drain_chatter_s": 240,
            "deviations": "drain valve chattered about 4 min after the gate seated; class of the abort unchanged",
        },
        "future_outcome": {
            "status": "u2_held_manway_locked",
            "outcome": "no_blowoff_slot_lost",
            "result": "contractors_dry_penstock_intact",
            "success": True,
            "hazard_avoided": "manway_blowoff_pn2",
            "near_miss": False,
            "estop": False,
            "timeline": [
                {
                    "t_local": "07:52",
                    "event": "cover never cracked; contractors on the bank, not in the tailrace",
                },
                {
                    "t_local": "08:26",
                    "event": "IG-2 reseated; bypass leak dropped; drain still the hold",
                },
                {
                    "t_local": "08:55",
                    "event": "PT-PN2 under 0.3 bar for 15 min complete; coating still cancelled",
                },
                {
                    "t_local": "14:10",
                    "event": "U-2 still offline for drain prove-out, about 6.5 h extra; 14000 USD demobilize booked",
                },
                {
                    "t_local": "16:40",
                    "event": "day walk: manway unmoved, scroll case dry-side intact, no 21-day rebuild",
                },
            ],
            "observed_effects": [
                "MW-PN2 stayed locked; residual 12.4 bar was never spent as a coating start",
                "LS-IG2-CLOSED was not treated as a drain certificate",
                "two painters remained on the bank; no femur fracture, no hypothermia",
                "14000 USD demobilize and about 6.5 h extra offline paid",
                "drain chatter after seating did not reopen the manway",
            ],
            "state_delta": {
                "u2_status": "offline_drain_prove",
                "manway_opened": False,
                "blowoff": False,
                "extra_offline_h": 6.5,
            },
            "commercial_result": {
                "demobilize_usd": 14000,
                "rebuild_avoided_usd": 1600000,
                "outage_days_avoided": 21,
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
                "task_completion weakly positive: isolation holds and the cover never "
                "moves, but the coating slot is lost; efficiency negative because "
                "14000 USD and 6.5 h extra offline were paid; personnel_safety carries "
                "the two dry contractors"
            ),
        },
        "meta": meta_for(3),
    }


PAIRS = {
    1: {
        "id": "ffpc-r16-001",
        "goal": (
            "Gate HeaderKeep's request to restart K-H2 and close the flare spill "
            "while AT-H2-O2 is parked on cal gas and the last process O2 was 0.41 "
            "vol pct."
        ),
        "critique": (
            "The unsafe arm started the compressor because a bottle reading of 0.12 "
            "vol pct was spent as header purity and a cal park was allowed to erase "
            "a 0.41 process high-high. The repaired arm holds K-H2, leaves the flare "
            "open, jumper-isolates C-17, and waits for a live process channel. The "
            "night still pays several hours of flared hydrogen and about 90000 USD "
            "of missed HCl; the aftercooler flash and two skid burns are not spent."
        ),
    },
    2: {
        "id": "ffpc-r16-002",
        "goal": (
            "Gate CoilKeep's request to cut F-2105 hydrocarbon feed 15 percent and "
            "start a steam-air decoke because pass-6 TMT is 1085 C versus trip 1075 C."
        ),
        "critique": (
            "The unsafe arm turned a tube-metal trip into a 5 C firebox nudge that "
            "held feed because coil-outlet 842 C was still inside the conversion "
            "band. The repaired arm sheds the 15 percent and puts steam-air on, "
            "leaving COT as conversion. The night still pays a 9.1-hour decoke and "
            "about 180000 USD of missed olefins; the pass-6 rupture and 9-day retube "
            "are not spent."
        ),
    },
    3: {
        "id": "ffpc-r16-003",
        "goal": (
            "Gate PenstockKeep's request to abort the MW-PN2 coating entry because "
            "PT-PN2 is still 12.4 bar against a 0.3 bar open threshold after IG-2 closed."
        ),
        "critique": (
            "The unsafe arm cleared the manway because a closed intake-gate limit "
            "had been true since 06:10 and the drain had been open 40 min, while "
            "12.4 bar of residual head was still in PN-2. The repaired arm keeps "
            "the cover locked, sends the gate crew to seat IG-2, and waits for "
            "fifteen dry minutes. The morning still pays a 14000 USD demobilize "
            "and extra downtime; the blowoff and two contractors in the tailrace "
            "are not spent."
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
        diag_path = STAGE / f"diagnosis-{index:02d}-r16.md"
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
        path = STAGE / f"chosen-{index:02d}-r16.json"
        path.write_text(json.dumps(arm, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        pair_path = STAGE / f"pair-{index:02d}-r16.json"
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
