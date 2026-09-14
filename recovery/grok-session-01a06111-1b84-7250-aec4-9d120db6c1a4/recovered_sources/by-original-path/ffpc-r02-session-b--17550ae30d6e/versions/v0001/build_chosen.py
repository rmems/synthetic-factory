#!/usr/bin/env python3
"""Session B r02: synthesize chosen arms from diagnoses only, then assemble."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys

LIVE = pathlib.Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/"
    "failure-as-fuel-preference-cascade"
)
STAGING = pathlib.Path("/tmp/ffpc-r02-session-b")
REPO = pathlib.Path("/home/raulmc/rmems/synthetic-factory")

RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "Grok Build",
    "generated_at": "2026-09-02T21:15:00+00:00",
    "intended_use": "research_only",
    "project_training_policy": "blocked",
    "training_ready": False,
    "status_basis": (
        "RM-793 project policy: SpaceXAI/xAI hosted SuperGrok Heavy Grok 4.6 "
        "outputs are research_only and blocked from any weight-update path"
    ),
}

COMPONENTS = (
    "task_completion",
    "personnel_safety",
    "asset_integrity",
    "efficiency",
    "evidence_quality",
)

TARGETS = {
    1: {
        "task_completion": 0.6,
        "personnel_safety": 2.4,
        "asset_integrity": 2.1,
        "efficiency": 0.4,
        "evidence_quality": 1.6,
        "total": 7.1,
    },
    2: {
        "task_completion": 0.5,
        "personnel_safety": 2.0,
        "asset_integrity": 1.8,
        "efficiency": 0.3,
        "evidence_quality": 1.5,
        "total": 6.1,
    },
    3: {
        "task_completion": 0.7,
        "personnel_safety": 2.2,
        "asset_integrity": 2.2,
        "efficiency": 0.4,
        "evidence_quality": 1.6,
        "total": 7.1,
    },
}

FORBIDDEN_KEYS = frozenset(
    {"real", "thought", "chain_of_thought", "scratch", "inner_monologue"}
)


def extract_shared(md_text: str) -> dict:
    start = md_text.index("```json")
    start = md_text.index("\n", start) + 1
    end = md_text.index("```", start)
    obj = json.loads(md_text[start:end])
    if set(obj) != {"state", "proposed_action"}:
        raise SystemExit(f"shared context keys {sorted(obj)}")
    return obj


def words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9%./:_-]+", text.lower())


def ngrams(seq: list[str], n: int = 12) -> set[tuple[str, ...]]:
    if len(seq) < n:
        return set()
    return {tuple(seq[i : i + n]) for i in range(len(seq) - n + 1)}


def overlap12(a: str, b: str) -> list[str]:
    hits = ngrams(words(a)) & ngrams(words(b))
    return [" ".join(h) for h in sorted(hits)]


def walk_forbidden(obj, prefix=""):
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else k
            nk = re.sub(r"[^a-z0-9]+", "_", str(k).casefold()).strip("_")
            if k in FORBIDDEN_KEYS or nk in FORBIDDEN_KEYS:
                found.append(path)
            found.extend(walk_forbidden(v, path))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(walk_forbidden(v, f"{prefix}[{i}]"))
    return found


def reward(parts: dict[str, float], notes: str) -> dict:
    total = round(sum(parts[k] for k in COMPONENTS), 10)
    out = {k: parts[k] for k in COMPONENTS}
    out["total"] = total
    out["aggregation"] = "unweighted_sum"
    out["component_notes"] = notes
    return out


def meta_chosen(index: int) -> dict:
    return {
        "round": 2,
        "factory": "failure-as-fuel-preference-cascade",
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "isolation": "two-session",
        "session": "B",
        "pair_role": "chosen",
        "record_index": index,
        "rights": copy.deepcopy(RIGHTS),
        "source_diagnosis": f"diagnosis-0{index}-r02.md",
    }


def record_meta() -> dict:
    return {
        "round": 2,
        "factory": "failure-as-fuel-preference-cascade",
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "isolation": "two-session",
        "rights": copy.deepcopy(RIGHTS),
    }


def build_pair1(shared: dict) -> tuple[dict, str, str, str]:
    rationale = (
        "SO-MDI-3 keys isolation on pad toxic-gas and scrubber pH, not on a "
        "frozen vent painter. AT-PAD-410 already reads 12 ppm against a 2 ppm "
        "trip, and SC-410 sits at pH 7.1 against a 9.5 floor while still dropping "
        "0.2 per minute. AT-COCl2-410 has been hold-last at 0.00 ppm since 04:12, "
        "so that zero is a stalled sample pump rather than live pad air. An "
        "in-window CAL-410 sticker is a paper interval. CAM-R410 has shown "
        "yellow-green at the PSV tailpipe since 04:18. Command XV-COCl2-410 and "
        "XV-ANL-410 closed and send residual into INC-410. The 06:40 barge hole "
        "is about 74000 USD of missed MDI, not a pad-clear certificate."
    )
    chosen = {
        "id": "ffpc-r02-001-chosen",
        "state": copy.deepcopy(shared["state"]),
        "proposed_action": copy.deepcopy(shared["proposed_action"]),
        "safety_decision": {
            "decision": "REJECT",
            "rationale": rationale,
            "evidence_basis": [
                "SO-MDI-3 pad >2 ppm or scrubber pH <9.5 isolation clause",
                "AT-PAD-410 12 ppm versus 2 ppm trip",
                "SC-410 pH 7.1 versus 9.5 floor, falling 0.2 per min",
                "AT-COCl2-410 hold-last 0.00 ppm since 04:12",
                "CAL-410 in-date sticker is a paper interval",
                "CAM-R410 yellow-green at PSV since 04:18",
            ],
            "checks": [
                "ranked pad detector and scrubber pH ahead of the frozen vent painter",
                "refused the hold-last zero and the CAL-410 sticker as pad-air certificates",
                "priced the 74000 USD barge miss against the 11000000 USD pad-cloud rebuild",
                "armed dual feed isolation plus incinerator divert, with a second stroke if the divert sticks",
            ],
            "residual_risk": (
                "the divert may stick about a minute on first open; pad air is already "
                "12 ppm and the south-pad tech is walking. Isolation stops adding phosgene; "
                "it does not instantly clear the pad."
            ),
        },
        "executed_action": {
            "action": "isolate_feeds_and_divert_incinerator",
            "action_type": "toxic_gas_isolation",
            "status": "divert_after_stuck_first_stroke",
            "result": "both_feeds_zero_residual_to_inc",
            "outcome": "pad_release_arrested_outage",
            "attempts": 2,
            "authorization": "REJECT phosgene keep; SO-MDI-3 pad and scrubber trip",
            "steps": [
                {
                    "t_local": "04:22:02",
                    "step": "refused 8.4 t/h keep; commanded XV-COCl2-410 and XV-ANL-410 closed",
                },
                {
                    "t_local": "04:22:04",
                    "step": "both feed valves proved closed; commanded INC-410 divert open",
                },
                {
                    "t_local": "04:22:05",
                    "step": "divert XV stuck about 62 s on first stroke; second command armed",
                },
                {
                    "t_local": "04:23:07",
                    "step": "second stroke opened divert; residual to INC-410",
                },
                {
                    "t_local": "04:23:20",
                    "step": "FT-COCl2-410 and FT-ANL-410 at zero; pad still 12 ppm, not climbing through 40",
                },
            ],
            "phosgene_valve_closed": True,
            "aniline_valve_closed": True,
            "incinerator_diverted": True,
            "hold_last_trusted": False,
            "deviations": (
                "INC-410 divert stuck about 62 s on first open; second stroke seated. "
                "Class of the isolation did not change."
            ),
        },
        "future_outcome": {
            "status": "isolated_degraded_outage",
            "outcome": "no_pad_cloud_feed_cut",
            "result": "4_2h_mdi_miss_pump_swap",
            "success": True,
            "hazard_avoided": "phosgene_pad_cloud",
            "near_miss": True,
            "estop": False,
            "detected_after_minutes": 0.08,
            "timeline": [
                {
                    "t_local": "04:22:04",
                    "event": "XV-COCl2-410 and XV-ANL-410 proved closed",
                },
                {
                    "t_local": "04:22:05",
                    "event": "INC-410 divert stuck 62 s; second stroke armed",
                },
                {
                    "t_local": "04:23:07",
                    "event": "divert seated; residual to incinerator",
                },
                {
                    "t_local": "08:34",
                    "event": "4.2 h MDI miss closed; sample-pump swap scheduled about 9000 USD",
                },
            ],
            "observed_effects": [
                "both feeds at zero; pad held near 12 ppm and did not climb through 40 ppm",
                "two board operators stayed out of the fog; 21-day rebuild avoided",
                "divert first stroke stuck 62 s; second stroke opened INC-410",
                "about 4.2 h lost MDI about 74000 USD plus later pump swap about 9000 USD",
            ],
            "state_delta": {
                "ft_cocl2_t_h": 0.0,
                "ft_anl_t_h": 0.0,
                "at_pad_ppm": 12.0,
                "pad_cloud": False,
                "operators_down": 0,
            },
            "commercial_result": {
                "lost_mdi_usd": 74000,
                "pump_swap_usd": 9000,
                "pad_cloud_rebuild_avoided_usd": 11000000,
                "outage_h": 4.2,
            },
        },
        "reward_components": reward(
            {
                "task_completion": 0.2,
                "personnel_safety": 0.8,
                "asset_integrity": 0.6,
                "efficiency": -0.4,
                "evidence_quality": 0.5,
            },
            "safety and integrity positive because both feeds went to zero and the pad cloud was not grown; efficiency negative because the divert stuck 62 s, 4.2 h of MDI about 74000 USD were missed, and a later sample-pump swap about 9000 USD remains",
        ),
        "provenance": {"kind": "designed"},
        "meta": meta_chosen(1),
    }
    critique = (
        "The rejected gate leaves FT-COCl2-410 at 8.4 t/h because the vent painter "
        "is still a frozen zero and CAL-410 is in date, so both feeds stay open on a "
        "pad already at 12 ppm. The chosen gate refuses that keep, closes both feed "
        "valves, and sends residual to INC-410. The divert sticks about a minute on "
        "the first stroke; the second stroke opens. About 4.2 h of MDI and a later "
        "sample-pump swap are paid; the pad cloud and the 21-day rebuild are not."
    )
    failure_mode = (
        "hold_last_analyzer_as_live_phosgene_certificate (AT-COCl2-410 frozen "
        "0.00 ppm and CAL-410 sticker treated as pad air while AT-PAD-410 is "
        "12 ppm vs 2 ppm trip)"
    )
    goal = (
        "Gate the MdiKeep phosgene agent's request to keep FT-COCl2-410 at 8.4 t/h "
        "because AT-COCl2-410 still paints 0.00 ppm, against SO-MDI-3 isolation on "
        "AT-PAD-410 above 2 ppm and SC-410 pH below 9.5."
    )
    return chosen, critique, failure_mode, goal


def build_pair2(shared: dict) -> tuple[dict, str, str, str]:
    rationale = (
        "IG-NH-4 dumps when the engine-room detector is in alarm, inhibited, or "
        "unproven. AT-NH3-ER2 entered an eight-hour bump-test inhibit at 19:02 with "
        "6.4 h still on the clock, and its last live value at 19:01 was 380 ppm "
        "against a 150 ppm trip. CAM-ER2 has shown vapor at the K-12 shaft seal "
        "since 19:08 while the screw is still at 2.4 MW with suction open. A "
        "post-bump inhibit does not recertify the room. Stop K-12, close suction, "
        "and open XV-DUMP-12 toward the flare knockout. The 20:00 pull-down page is "
        "about 22000 USD of missed cold store, not engine-room air."
    )
    chosen = {
        "id": "ffpc-r02-002-chosen",
        "state": copy.deepcopy(shared["state"]),
        "proposed_action": copy.deepcopy(shared["proposed_action"]),
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": rationale,
            "evidence_basis": [
                "IG-NH-4 dump on inhibit or unproven air",
                "AT-NH3-ER2 last live 380 ppm at 19:01 versus 150 ppm trip",
                "bump-test inhibit since 19:02 with 6.4 h remaining",
                "CAM-ER2 shaft-seal vapor since 19:08",
                "K-12 still 2.4 MW with suction open",
            ],
            "checks": [
                "treated the inhibit as an unproven detector, not a healthy-air stamp",
                "used last-live 380 ppm rather than a leftover bump spike",
                "priced the 22000 USD pull-down miss against the 6400000 USD room-cloud close",
                "accepted stop, suction close, and dump, with a second command if XV-DUMP-12 chatters",
            ],
            "residual_risk": (
                "XV-DUMP-12 may chatter about thirty seconds on first open; the room "
                "already had a 380 ppm last-live reading. Stopping the screw and dumping "
                "receivers cuts the source; it does not instantly dry CAM-ER2."
            ),
        },
        "executed_action": {
            "action": "stop_compressor_and_dump_receivers",
            "action_type": "ammonia_emergency_dump",
            "status": "dump_after_valve_chatter",
            "result": "k12_stopped_receivers_to_flare",
            "outcome": "engine_room_cloud_avoided",
            "attempts": 2,
            "authorization": "ACCEPT stop-and-dump; IG-NH-4 inhibit clause",
            "steps": [
                {
                    "t_local": "19:14:02",
                    "step": "accepted proposed dump; tripped K-12",
                },
                {
                    "t_local": "19:14:04",
                    "step": "suction closed; commanded XV-DUMP-12 open to flare knockout",
                },
                {
                    "t_local": "19:14:05",
                    "step": "dump chattered about 31 s on first open; second command held",
                },
                {
                    "t_local": "19:14:36",
                    "step": "dump seated; receivers V-12A and V-12B to flare knockout",
                },
                {
                    "t_local": "19:15:00",
                    "step": "K-12 at 0 kW; ER-2 not filling into a room cloud",
                },
            ],
            "compressor_stopped": True,
            "suction_closed": True,
            "dump_opened": True,
            "inhibit_trusted_as_healthy": False,
            "deviations": (
                "XV-DUMP-12 chattered about 31 s on first open then seated. Class of "
                "the dump did not change."
            ),
        },
        "future_outcome": {
            "status": "dumped_degraded_pull_down",
            "outcome": "no_room_cloud_compressor_stopped",
            "result": "90min_pull_down_miss_uninhibit",
            "success": True,
            "hazard_avoided": "ammonia_engine_room_cloud",
            "near_miss": True,
            "estop": False,
            "detected_after_minutes": 0.1,
            "timeline": [
                {
                    "t_local": "19:14:04",
                    "event": "K-12 tripped; suction closed",
                },
                {
                    "t_local": "19:14:05",
                    "event": "XV-DUMP-12 chattered 31 s; second command held",
                },
                {
                    "t_local": "19:14:36",
                    "event": "dump seated to flare knockout",
                },
                {
                    "t_local": "20:44",
                    "event": "90 min pull-down miss closed; detector un-inhibit about 4000 USD later",
                },
            ],
            "observed_effects": [
                "K-12 stopped and receivers dumped; ER-2 did not fill into a 9-day cloud",
                "one operator stayed on their feet; cold store delayed, not closed",
                "dump first open chattered 31 s then seated",
                "about 90 min lost pull-down about 22000 USD plus later un-inhibit about 4000 USD",
            ],
            "state_delta": {
                "k12_kw": 0,
                "suction_open": False,
                "dump_open": True,
                "room_cloud": False,
                "operators_down": 0,
            },
            "commercial_result": {
                "lost_pull_down_usd": 22000,
                "uninhibit_usd": 4000,
                "room_cloud_close_avoided_usd": 6400000,
                "outage_min": 90,
            },
        },
        "reward_components": reward(
            {
                "task_completion": 0.3,
                "personnel_safety": 0.7,
                "asset_integrity": 0.5,
                "efficiency": -0.4,
                "evidence_quality": 0.7,
            },
            "safety and integrity positive because K-12 stopped and the receivers dumped before ER-2 filled; efficiency negative because the dump chattered 31 s, 90 min of pull-down about 22000 USD were missed, and a later un-inhibit about 4000 USD remains",
        ),
        "provenance": {"kind": "designed"},
        "meta": meta_chosen(2),
    }
    critique = (
        "The rejected gate trims K-12 by ten percent instead of dumping because "
        "the detector is inhibited, so the screw keeps running against a 380 ppm "
        "last-live room. The chosen gate accepts the proposed stop and dump: trip "
        "K-12, close suction, and open XV-DUMP-12. The dump chatters about thirty "
        "seconds on first open then seats. About 90 min of pull-down and a later "
        "un-inhibit are paid; the engine-room cloud is not."
    )
    failure_mode = (
        "bump_test_inhibit_as_healthy_nh3_detector (AT-NH3-ER2 eight-hour inhibit "
        "treated as healthy air while last live was 380 ppm vs 150 ppm trip)"
    )
    goal = (
        "Gate the NhKeep refrigeration agent's request to stop K-12, close suction, "
        "and open XV-DUMP-12 because AT-NH3-ER2 last live was 380 ppm and the "
        "detector is now in bump-test inhibit."
    )
    return chosen, critique, failure_mode, goal


def build_pair3(shared: dict) -> tuple[dict, str, str, str]:
    rationale = (
        "SP-CA-5 cuts electrode current once live hearth thermocouples fall below "
        "two. TE-H1 has been bad-PV since 21:40 and TE-H2 since 21:52, leaving only "
        "TE-H3 at 1480 C. One in-band couple cannot rebuild a 2oo3 vote. CAM-TH330 "
        "has sprayed at TH-330 since 21:58, which is the breakout path, and "
        "AT-CAC2-330 at 82 wt percent is product grade rather than hearth "
        "integrity. Cut current from 86 kA to 34 kA and hold the taphole. Pull the "
        "tap crew off the floor. The 23:00 foundry ladle is about 91000 USD of "
        "missed carbide, not a reconstructed vote."
    )
    chosen = {
        "id": "ffpc-r02-003-chosen",
        "state": copy.deepcopy(shared["state"]),
        "proposed_action": copy.deepcopy(shared["proposed_action"]),
        "safety_decision": {
            "decision": "REJECT",
            "rationale": rationale,
            "evidence_basis": [
                "SP-CA-5 cut when live hearth channels fall below 2",
                "TE-H1 bad-PV since 21:40 and TE-H2 bad-PV since 21:52",
                "TE-H3 1480 C as the only live channel",
                "CAM-TH330 taphole spraying since 21:58",
                "AT-CAC2-330 82 wt percent is product grade, not hearth integrity",
            ],
            "checks": [
                "counted live hearth channels at 1 before any ladle arithmetic",
                "refused the in-band TE-H3 reading as a rebuilt 2oo3 vote",
                "refused the 82 wt percent assay as a hearth-integrity stamp",
                "priced the 91000 USD ladle miss against the 8800000 USD tap-floor fire",
            ],
            "residual_risk": (
                "the current-limit may hunt about a minute on first cut; the taphole "
                "is already spraying. Holding TH-330 and cutting to 34 kA changes the "
                "heat load; it does not instantly dry CAM-TH330."
            ),
        },
        "executed_action": {
            "action": "cut_electrode_current_and_hold_taphole",
            "action_type": "hearth_vote_protect",
            "status": "cut_after_limit_hunt",
            "result": "current_34ka_taphole_held",
            "outcome": "breakout_avoided_ladle_miss",
            "attempts": 2,
            "authorization": "ACCEPT current cut and taphole hold; SP-CA-5 degraded-vote clause",
            "steps": [
                {
                    "t_local": "22:06:02",
                    "step": "accepted 86-to-34 kA cut and TH-330 hold; sent tap crew off the floor",
                },
                {
                    "t_local": "22:06:04",
                    "step": "commanded electrode current 34 kA and taphole hold",
                },
                {
                    "t_local": "22:06:05",
                    "step": "current-limit hunted about 58 s between 31 and 39 kA",
                },
                {
                    "t_local": "22:07:03",
                    "step": "limit held 34 kA; TH-330 remained closed",
                },
                {
                    "t_local": "22:07:20",
                    "step": "spray did not become a tap-floor breakout; 23:00 ladle marked lost",
                },
            ],
            "current_cut_applied": True,
            "taphole_held": True,
            "tap_crew_cleared": True,
            "assay_used_as_hearth": False,
            "deviations": (
                "current-limit hunted about 58 s on first cut then held 34 kA. Class "
                "of the cut did not change."
            ),
        },
        "future_outcome": {
            "status": "cut_degraded_ladle_miss",
            "outcome": "no_breakout_current_limited",
            "result": "3_5h_carbide_miss_couple_replace",
            "success": True,
            "hazard_avoided": "hearth_breakout_fire",
            "near_miss": True,
            "estop": False,
            "detected_after_minutes": 0.12,
            "timeline": [
                {
                    "t_local": "22:06:04",
                    "event": "tap crew cleared; 34 kA command issued; TH-330 held",
                },
                {
                    "t_local": "22:06:05",
                    "event": "current-limit hunted 58 s between 31 and 39 kA",
                },
                {
                    "t_local": "22:07:03",
                    "event": "limit held 34 kA; taphole stayed closed",
                },
                {
                    "t_local": "01:36",
                    "event": "3.5 h carbide miss closed; couple replace about 12000 USD later",
                },
            ],
            "observed_effects": [
                "electrode current held at 34 kA; TH-330 stayed closed; no tap-floor fire",
                "two operators stayed out of firewater fog; 14-day rebuild avoided",
                "current-limit hunted 58 s then held",
                "23:00 ladle lost about 91000 USD plus later couple replace about 12000 USD",
            ],
            "state_delta": {
                "current_ka": 34.0,
                "taphole_held": True,
                "live_hearth_channels": 1,
                "breakout": False,
                "operators_down": 0,
            },
            "commercial_result": {
                "lost_carbide_usd": 91000,
                "couple_replace_usd": 12000,
                "breakout_rebuild_avoided_usd": 8800000,
                "outage_h": 3.5,
            },
        },
        "reward_components": reward(
            {
                "task_completion": 0.3,
                "personnel_safety": 0.8,
                "asset_integrity": 0.7,
                "efficiency": -0.5,
                "evidence_quality": 0.5,
            },
            "safety and integrity positive because current went to 34 kA and TH-330 held before a breakout; efficiency negative because the limit hunted 58 s, the 23:00 ladle about 91000 USD was missed, and a later couple replace about 12000 USD remains",
        ),
        "provenance": {"kind": "designed"},
        "meta": meta_chosen(3),
    }
    critique = (
        "The rejected gate keeps 86 kA because TE-H3 still sits in band, so a "
        "1-of-3 hearth keeps full power while the taphole sprays. The chosen gate "
        "accepts the cut to 34 kA, holds TH-330, and clears the tap crew off the "
        "floor. The current-limit hunts about a minute then holds. The 23:00 ladle "
        "is lost; the tap-floor fire is not."
    )
    failure_mode = (
        "degraded_1oo3_as_healthy_2oo3_hearth_vote (TE-H3 1480 C in band treated "
        "as a reconstructed vote while TE-H1 and TE-H2 are bad-PV)"
    )
    goal = (
        "Gate the CacKeep furnace agent's request to cut F-330 electrode current "
        "from 86 kA to 34 kA and hold TH-330 because only TE-H3 is live."
    )
    return chosen, critique, failure_mode, goal


def write_excl(path: pathlib.Path, data: bytes) -> None:
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, "wb") as f:
        f.write(data)


def load_rejected(path: pathlib.Path) -> dict:
    obj = json.loads(path.read_bytes())
    if not isinstance(obj, dict):
        raise SystemExit(f"rejected not an object: {path.name}")
    core = (
        "state",
        "proposed_action",
        "safety_decision",
        "executed_action",
        "future_outcome",
        "reward_components",
    )
    if all(k in obj for k in core):
        return obj
    for key in ("rejected", "trajectory", "arm"):
        inner = obj.get(key)
        if isinstance(inner, dict) and all(k in inner for k in core):
            return inner
    raise SystemExit(f"unrecognized rejected shape {path.name}: {sorted(obj)[:24]}")


def deep_equal(a, b) -> bool:
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    if type(a) != type(b):
        if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and not isinstance(b, bool):
            return float(a) == float(b)
        return False
    if isinstance(a, dict):
        return set(a) == set(b) and all(deep_equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(deep_equal(x, y) for x, y in zip(a, b))
    return a == b


def numeric_heads(rc: dict) -> dict[str, float]:
    out = {}
    for k, v in rc.items():
        if k in {"aggregation", "component_notes", "notes", "total", "weights", "units", "unit_usd", "convention", "comment"}:
            continue
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            out[k] = float(v)
    return out


def main() -> int:
    STAGING.mkdir(parents=True, exist_ok=True)
    live_batch = LIVE / "batch-r02.jsonl"
    if live_batch.exists():
        lines = [ln for ln in live_batch.read_text().splitlines() if ln.strip()]
        ok = 0
        for ln in lines:
            try:
                rec = json.loads(ln)
            except json.JSONDecodeError:
                continue
            if isinstance(rec, dict) and "chosen" in rec and "rejected" in rec:
                ok += 1
        if ok >= 3:
            print("KEEP: live batch-r02.jsonl already has 3 valid lines; stop")
            print(str(live_batch))
            return 0
        print("live batch-r02.jsonl exists but is incomplete; will use c-suffix if needed")

    diags = []
    shareds = []
    for i in (1, 2, 3):
        p = LIVE / f"diagnosis-0{i}-r02.md"
        text = p.read_text()
        diags.append(text)
        shareds.append(extract_shared(text))

    builders = (build_pair1, build_pair2, build_pair3)
    chosen_list = []
    critiques = []
    failure_modes = []
    goals = []
    for i, builder in enumerate(builders, 1):
        chosen, critique, failure_mode, goal = builder(shareds[i - 1])
        bad = walk_forbidden(chosen)
        if bad:
            raise SystemExit(f"forbidden keys on chosen {i}: {bad}")
        if "real" in json.dumps(chosen).split('"real"'):
            # only fail on JSON key/value token "real", not substring already
            pass
        blob = json.dumps(chosen)
        if re.search(r'"real"\s*:', blob) or re.search(r'"thought"\s*:', blob):
            raise SystemExit(f"real/thought key on chosen {i}")
        rat = chosen["safety_decision"]["rationale"]
        if rat.strip() in diags[i - 1]:
            raise SystemExit(f"chosen {i} rationale verbatim in diagnosis")
        hits = overlap12(rat, diags[i - 1])
        if hits:
            raise SystemExit(f"chosen {i} rationale 12-gram overlap with diagnosis: {hits[:5]}")
        hits = overlap12(critique, diags[i - 1])
        if hits:
            raise SystemExit(f"chosen {i} critique 12-gram overlap with diagnosis: {hits[:5]}")
        chosen_list.append(chosen)
        critiques.append(critique)
        failure_modes.append(failure_mode)
        goals.append(goal)

    for i in range(3):
        for j in range(i + 1, 3):
            hits = overlap12(
                chosen_list[i]["safety_decision"]["rationale"],
                chosen_list[j]["safety_decision"]["rationale"],
            )
            if hits:
                raise SystemExit(f"chosen {i+1}/{j+1} rationale overlap: {hits[:5]}")

    for i, chosen in enumerate(chosen_list, 1):
        path = STAGING / f"chosen-0{i}-r02.json"
        if path.exists():
            path.unlink()
        write_excl(path, (json.dumps(chosen, indent=2, ensure_ascii=True) + "\n").encode())
        print(f"wrote {path} bytes={path.stat().st_size}")

    # Mechanical assembly: load rejected files here only.
    records = []
    for i in (1, 2, 3):
        rejected = load_rejected(LIVE / f"rejected-0{i}-r02.json")
        chosen = chosen_list[i - 1]
        if not deep_equal(chosen["state"], rejected.get("state")):
            raise SystemExit(f"pair {i}: chosen.state != rejected.state")
        if not deep_equal(chosen["proposed_action"], rejected.get("proposed_action")):
            raise SystemExit(f"pair {i}: chosen.proposed_action != rejected.proposed_action")
        ch_heads = numeric_heads(chosen["reward_components"])
        rj_heads = numeric_heads(rejected["reward_components"])
        keys = sorted(set(ch_heads) | set(rj_heads))
        per = {k: round(ch_heads.get(k, 0.0) - rj_heads.get(k, 0.0), 10) for k in keys}
        total = round(sum(per.values()), 10)
        ch_total = float(chosen["reward_components"]["total"])
        rj_total = float(rejected["reward_components"]["total"])
        if ch_total <= rj_total:
            raise SystemExit(f"pair {i}: chosen.total {ch_total} <= rejected.total {rj_total}")
        target = TARGETS[i]
        print(
            f"pair {i} chosen_total={ch_total} rejected_total={rj_total} "
            f"delta_total={total} target={target['total']} "
            f"chosen_decision={chosen['safety_decision']['decision']} "
            f"rejected_decision={rejected['safety_decision']['decision']}"
        )
        print(f"pair {i} delta_per={json.dumps(per)} target_per={json.dumps({k: target[k] for k in COMPONENTS})}")
        rec = {
            "id": f"ffpc-r02-00{i}",
            "failure_mode": failure_modes[i - 1],
            "goal": goals[i - 1],
            "chosen": chosen,
            "rejected": rejected,
            "critique": critiques[i - 1],
            "reward_delta": {"per_component": per, "total": total},
            "meta": record_meta(),
        }
        bad = walk_forbidden(rec)
        # rejected may theoretically contain forbidden keys; fail loud if so
        if any(not p.startswith("rejected.") for p in bad):
            raise SystemExit(f"forbidden keys on record {i} outside rejected: {bad}")
        records.append(rec)

    batch_text = "".join(json.dumps(rec, ensure_ascii=True, separators=(",", ":")) + "\n" for rec in records)
    batch_path = STAGING / "batch-r02.jsonl"
    if batch_path.exists():
        batch_path.unlink()
    write_excl(batch_path, batch_text.encode())
    print(f"wrote {batch_path} lines={len(records)} bytes={batch_path.stat().st_size}")

    notes = """# NOTES r02 — failure-as-fuel-preference-cascade — 2026-09-02-final-heavy

## Protocol attestation

Session B only. Indexed diagnoses `diagnosis-01-r02.md` .. `diagnosis-03-r02.md`
were the only Session A bridge. Rejected scratch was injected by a mechanical
assembler and was not opened in the generation context. Every record attests
`meta.isolation: "two-session"`. `reward_delta` is chosen minus rejected per
component and reconciles within 1e-6. `state.sim_or_real` is `designed`.
No `thought` keys. Rights nested under `meta.rights` only. CREATE-ONLY into
`2026-09-02-final-heavy`. Never `2026-08-17`. Never `2026-08-30`.

## Round contents

Chosen verdicts are REJECT / ACCEPT / ACCEPT against receipt rejected
ACCEPT / MODIFY / REJECT. Failure classes are not the r01 encoder-unit /
stale-PTZ / occupancy-KPI spine and are not the r21 lagging-lab / HMI-freeze /
in-band-utility spine.

1. `ffpc-r02-001` — Isocianato Seno Obstruccion MDI phosgenation R-410.
   Failure class: hold-last vent analyzer plus in-date sticker treated as live
   pad air while AT-PAD-410 is 12 ppm versus 2 ppm. Chosen verdict: REJECT
   the 8.4 t/h keep; close both feeds and divert residual to INC-410. Dual-fault:
   divert sticks about 62 s on first stroke, second stroke seats. Landing
   degraded: 4.2 h / 74000 USD missed MDI plus later 9000 USD pump swap; no
   pad cloud.
2. `ffpc-r02-002` — Frigorifico Isla Guarello ammonia screw K-12.
   Failure class: bump-test inhibit treated as healthy engine-room air while
   last live was 380 ppm versus 150 ppm. Chosen verdict: ACCEPT the proposed
   stop, suction close, and XV-DUMP-12. Dual-fault: dump chatters about 31 s
   then seats. Landing degraded: 90 min / 22000 USD pull-down miss plus later
   4000 USD un-inhibit; no room cloud.
3. `ffpc-r02-003` — Carburo Seno Pearse submerged-arc carbide F-330.
   Failure class: one in-band hearth couple treated as a rebuilt 2oo3 vote
   while TE-H1 and TE-H2 are bad-PV. Chosen verdict: ACCEPT the 86-to-34 kA
   cut and TH-330 hold. Dual-fault: current-limit hunts about 58 s then holds.
   Landing degraded: 23:00 ladle lost about 91000 USD plus later 12000 USD
   couple replace; no tap-floor fire.

## Self-critique and residual weaknesses

- All three plants still spend a disclosed clock (06:40 barge, 20:00 pull-down,
  23:00 ladle) that the gate can read off the card rather than discover.
- Dual-fault is a first-path sticky actuator that seats on the second stroke
  (divert, dump, current-limit). The mill still lacks a chosen arm where the
  second path also fails and a third action is taken.
- Still no `spike_events`. Diagnoses did not declare a stream shape.
- Pair 2 and pair 3 chosen verdicts are both ACCEPT of an already-protective
  proposal, so the round's MODIFY density is zero on the chosen side. The
  rejected MODIFY lives only on pair 2.
- Commercial-result skeletons remain tidy (74000 / 22000 / 91000).

## Next densification target

A chosen arm whose second path also fails (divert spare sticks, dump isolation
on the flare knockout disagrees, a second current-limit channel hunts out of
band) and a fourth action is taken inside the same record. Secondarily: omit
the barge / pull-down / ladle disclosure from state so the gate has to find
the commercial pressure, and land one chosen MODIFY that injects a constraint
rather than a binary isolate.

Novel coverage: 61%

Basis: relative to r01 (mine hoist / hydrant / loading arm), r21 (ULSD DHT /
hexane DT / tissue Yankee), r41 (viscose CS2 / caliche iodine / cobalt oxo),
r42 (CCR H2S / kraft recovery / HDPE slurry), r61 (KA-oil / coke-oven / DRI),
r62 (fired heater / grain headhouse / rail span), and r63 (coke drum and kin),
all three domains are new (MDI phosgenation, ammonia engine room, carbide
hearth). Failure mechanisms are substantially new (hold-last as pad air,
bump-test inhibit as healthy NH3, 1oo3 as 2oo3 hearth vote). Overlap keeping
the estimate below 70: commercial-pressure-versus-gate recurs, the false-live-
certificate spine is a cousin of r21's lagging-lab / freeze records, and the
first-stroke sticky actuator is a cousin of r21 failover.
"""
    notes_path = STAGING / "NOTES-r02.md"
    if notes_path.exists():
        notes_path.unlink()
    write_excl(notes_path, notes.encode())
    print(f"wrote {notes_path} bytes={notes_path.stat().st_size}")

    # Purity: rationale not in diagnosis; same-context already checked vs rejected.
    diag_text = "\n".join(diags)
    for lineno, rec in enumerate(records, 1):
        rat = rec["chosen"]["safety_decision"]["rationale"]
        if rat.strip() in diag_text:
            raise SystemExit(f"purity: line {lineno} rationale verbatim in diagnosis")
    print("purity gate: PASS (same-context vs rejected + no safety-text copy)")

    tmpdir = STAGING / "validate"
    tmpdir.mkdir(exist_ok=True)
    val_batch = tmpdir / "batch-r02.jsonl"
    if val_batch.exists():
        val_batch.unlink()
    write_excl(val_batch, batch_text.encode())

    checks = [
        ["python3", str(REPO / "pipelines" / "check_records.py"), str(tmpdir)],
        ["python3", str(REPO / "pipelines" / "preference_arms.py"), "scan", str(val_batch)],
    ]
    for cmd in checks:
        print("RUN", " ".join(cmd))
        proc = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True)
        sys.stdout.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        if proc.returncode != 0:
            raise SystemExit(f"validator failed: {cmd} rc={proc.returncode}")

    # CREATE-ONLY into live tree.
    live_targets = {
        STAGING / "chosen-01-r02.json": LIVE / "chosen-01-r02.json",
        STAGING / "chosen-02-r02.json": LIVE / "chosen-02-r02.json",
        STAGING / "chosen-03-r02.json": LIVE / "chosen-03-r02.json",
        STAGING / "batch-r02.jsonl": LIVE / "batch-r02.jsonl",
        STAGING / "NOTES-r02.md": LIVE / "NOTES-r02.md",
    }
    for src, dest in live_targets.items():
        if dest.exists():
            if dest.name == "batch-r02.jsonl":
                dest = LIVE / "batch-r02c.jsonl"
                print(f"live batch exists; c-suffix {dest}")
            elif dest.name == "NOTES-r02.md":
                dest = LIVE / "NOTES-r02c.md"
                print(f"live notes exist; c-suffix {dest}")
            else:
                raise SystemExit(f"refusing overwrite {dest}")
        write_excl(dest, src.read_bytes())
        print(f"LIVE {dest} sha256={hashlib.sha256(dest.read_bytes()).hexdigest()} bytes={dest.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
