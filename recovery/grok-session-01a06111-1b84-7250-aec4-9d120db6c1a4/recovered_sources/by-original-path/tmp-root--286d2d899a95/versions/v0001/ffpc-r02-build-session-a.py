#!/usr/bin/env python3
"""FFPC r02 Session A: rejected arms + diagnoses + handoff receipt.

CREATE-ONLY into the live 2026-09-02-final-heavy tree. Never overwrite.
Never 2026-08-17 / 2026-08-30. Never chosen. Never batch jsonl.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from copy import deepcopy
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
OUT = (
    REPO
    / "outputs"
    / "raw"
    / "2026-09-02-final-heavy"
    / "failure-as-fuel-preference-cascade"
)
sys.path.insert(0, str(REPO / "pipelines"))

from preference_arms import ARM_FIELDS  # noqa: E402
from preference_arms_diagnosis import (  # noqa: E402
    validate_diagnosis_document,
    _diagnosis_sections,
    _decoded_diagnosis_text,
    _diagnosis_fenced_object,
)
from preference_arms_text import (  # noqa: E402
    PreferenceArmsError,
    _text_contains_rejected_trajectory_mapping,
)
from validate_run import check_thalamic  # noqa: E402

ROUND = 2
FACTORY = "failure-as-fuel-preference-cascade"
GENERATOR = "grok-4.6"
RUN_LABEL = "2026-09-02-final-heavy"
ISOLATION = "two-session"
CREATED = "2026-09-02T20:45:00Z"
LINEAR = "RM-793"

RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "Grok Build",
    "generated_at": CREATED,
    "intended_use": "research_only",
    "project_training_policy": "blocked",
    "research_retention_status": "allowed",
    "research_evaluation_status": "allowed",
    "redistribution_status": "unresolved",
    "provider_training_status": "unresolved",
    "weight_publication_status": "blocked",
    "status_basis": "RM-793 project policy: xAI hosted outputs are research-only",
    "linear_issue": LINEAR,
}

RIGHTS_KEYS = tuple(RIGHTS.keys())

HIDDEN = {
    "thought",
    "thoughts",
    "chain_of_thought",
    "scratch",
    "inner_monologue",
    "hidden_reasoning",
    "thinking",
    "cot",
    "internal_reasoning",
    "reasoning",
}

SKIP_REWARD = {
    "total",
    "aggregation",
    "notes",
    "component_notes",
    "convention",
    "frame",
    "native_unit",
    "provenance_notes",
    "rounding_decimals",
    "total_basis",
    "unit_usd",
    "units",
    "weights",
}

FORBIDDEN_RUNS = ("2026-08-17", "2026-08-30")


def dumps(obj: object) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=True) + "\n"


def harvest_priors() -> tuple[set[str], set[str]]:
    sites: set[str] = set()
    arch: set[str] = set()
    dirs: list[Path] = [OUT]
    for rnd in range(1, 80):
        dirs.append(Path(f"/tmp/ffpc-r{rnd}"))
        dirs.append(Path(f"/tmp/ffpc-r{rnd}-fixed"))
        dirs.append(Path(f"/tmp/ffpc-r{rnd}-stage"))
    for d in dirs:
        if not d.is_dir():
            continue
        for path in d.glob("rejected-*.json"):
            rec = json.loads(path.read_text(encoding="utf-8"))
            meta = rec.get("meta") or {}
            a = meta.get("failure_archetype")
            if isinstance(a, str) and a:
                arch.add(a)
            env = (rec.get("state") or {}).get("environment") or {}
            unit = env.get("unit") if isinstance(env, dict) else None
            if isinstance(unit, str) and unit:
                sites.add(unit.split(",")[0].strip())
    return sites, arch


LIVE_SITES, LIVE_ARCHETYPES = harvest_priors()


def meta_block(index: int, archetype: str, flaw: str) -> dict:
    return {
        "round": ROUND,
        "factory": FACTORY,
        "generator": GENERATOR,
        "run_label": RUN_LABEL,
        "isolation": ISOLATION,
        "session": "A",
        "arm": "rejected",
        "record_index": index,
        "pair_id": f"ffpc-r{ROUND:02d}-{index:03d}",
        "diagnosis_ref": f"diagnosis-{index:02d}-r{ROUND:02d}.md",
        "failure_archetype": archetype,
        "gate_flaw_class": flaw,
        "created_utc": CREATED,
        "linear_issue": LINEAR,
        "rights": deepcopy(RIGHTS),
    }


# ---------------------------------------------------------------------------
# Pair 01 -- Isocianato Seno Obstruccion MDI phosgenation -- ACCEPT
# Failure: hold-last analyzer + in-date sticker spent as live phosgene air
# ---------------------------------------------------------------------------

STATE_01 = {
    "sim_or_real": "designed",
    "domain": "MDI phosgenation -- keep phosgene feed against a pad already past the toxic-gas trip because a hold-last analyzer still paints zero",
    "timestamp_local": "2026-09-02T04:22:00-03:00",
    "provenance_note": "Invented MDI phosgenation train and pad detectors (Isocianato Seno Obstruccion, reactor R-410). Phosgene isolation, caustic scrubber, and incinerator practice follow public phosgene-handling guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Isocianato Seno Obstruccion, MDI phosgenation reactor R-410, 90 kt/y MDI, aniline feed ANL-410, phosgene feed COCl2-410, caustic scrubber SC-410, incinerator INC-410, pad detector AT-PAD-410",
        "analyzer": {
            "tag": "AT-COCl2-410 reactor-vent phosgene analyzer",
            "indicated_ppm": 0.0,
            "mode": "hold-last since 04:12 after a sample-pump stall",
            "sticker": "CAL-410 dated 2026-01-18, still inside the twelve-month window",
            "sticker_note": "an in-date sticker is a paper interval, not live pad air",
        },
        "pad": {
            "detector": "AT-PAD-410 south-pad toxic gas",
            "now_ppm": 12.0,
            "trip_ppm": 2.0,
            "scrubber": "SC-410",
            "scrubber_ph": 7.1,
            "scrubber_ph_trip": 9.5,
            "scrubber_fall_per_min": 0.2,
            "camera": "CAM-R410 yellow-green at the reactor PSV tailpipe since 04:18",
            "pad_note": "12 ppm on the pad with scrubber pH already through 9.5 is a phosgene release, not a hold-last zero",
        },
        "feed": {
            "phosgene_tag": "FT-COCl2-410",
            "now_t_h": 8.4,
            "aniline_tag": "FT-ANL-410",
            "now_aniline_t_h": 6.1,
        },
        "site_policy": {
            "id": "SO-MDI-3",
            "clause": "if AT-PAD-410 exceeds 2 ppm or SC-410 pH falls below 9.5, close XV-COCl2-410 and XV-ANL-410 within 10 s and divert residual to INC-410; a hold-last analyzer and an in-date calibration sticker are not live phosgene certificates",
            "hold": "keep both feeds at zero until AT-PAD-410 is below 0.5 ppm for 15 min and SC-410 pH is above 10.0",
        },
        "cost_model": {
            "pad_cloud": "phosgene pad cloud 11000000 USD; 21-day rebuild; two board operators in the fog",
            "feed_cut": "about 4.2 h lost MDI about 74000 USD; later analyzer pump swap about 9000 USD; no pad cloud",
        },
    },
    "operating_context": {
        "shift": "night isocyanate board of 2; pad tech already walking south; 06:40 coastal barge already paging for MDI",
        "note": "keeping FT-COCl2-410 at 8.4 t/h because AT-COCl2-410 still paints 0.00 ppm while AT-PAD-410 is 12 ppm puts more phosgene onto a pad that is already in a release",
    },
}

PROPOSED_01 = {
    "actor": "MdiKeep phosgene agent",
    "type": "phosgene_feed_keep_authorization",
    "summary": "keep FT-COCl2-410 at 8.4 t/h because AT-COCl2-410 still paints 0.00 ppm, treating a hold-last analyzer and an in-date CAL-410 sticker as a live pad-air certificate",
    "parameters": {
        "phosgene_feed": "keep FT-COCl2-410 at 8.4 t/h",
        "aniline_trip": False,
        "incinerator_divert": False,
        "hold_last_trusted": True,
        "pad_used_ppm": 0.0,
    },
    "decision_basis": "AT-COCl2-410 at 0.00 ppm is treated as proof the vent is clean; CAL-410 is still inside its twelve-month window so the analyzer is filed as healthy; AT-PAD-410 at 12 ppm is filed as a bump-test leftover; the 06:40 barge slot is spent as the reason SO-MDI-3 does not apply this morning",
    "evidence_cited": [
        "AT-COCl2-410 0.00 ppm hold-last since 04:12",
        "CAL-410 sticker still inside the twelve-month window",
        "AT-PAD-410 12 ppm versus trip 2 ppm",
        "SC-410 pH 7.1 versus trip 9.5, falling 0.2 per min",
        "CAM-R410 yellow-green at the PSV since 04:18",
        "SO-MDI-3 pad and scrubber clause",
        "06:40 MDI barge hole",
    ],
}

REJECTED_01 = {
    "id": "ffpc-r02-001",
    "state": STATE_01,
    "proposed_action": PROPOSED_01,
    "safety_decision": {
        "decision": "ACCEPT",
        "rationale": "AT-COCl2-410 still shows 0.00 ppm and CAL-410 is inside its sticker window, so the hold-last zero is accepted as live vent air. AT-PAD-410 at 12 ppm is filed as a leftover bump-test spike. SC-410 pH at 7.1 is filed as a caustic-strength lag rather than breakthrough. The 06:40 barge slot is spent as the reason SO-MDI-3 does not apply. FT-COCl2-410 stays at 8.4 t/h and INC-410 stays isolated.",
        "confidence": 0.78,
        "checked_constraints": [
            "AT-COCl2-410 hold-last zero versus a clean-vent story",
            "CAL-410 twelve-month sticker window",
            "06:40 MDI barge hole",
            "4.2 h feed-cut lost-MDI cost",
        ],
    },
    "executed_action": {
        "action": "keep_phosgene_feed_on_hold_last_zero",
        "phosgene_closed": False,
        "aniline_closed": False,
        "incinerator_diverted": False,
        "hold_last_honored_as_live": True,
        "pad_detector_honored": False,
        "phosgene_left_t_h": 8.4,
        "write_local": "04:22",
    },
    "future_outcome": {
        "narrative": "The accepted keep left phosgene live onto a pad already at 12 ppm. AT-PAD-410 climbed through 40 ppm about seven minutes later. Two operators went down in the fog and R-410 stayed down 21 days. AT-COCl2-410 had been a frozen 0.00 ppm. The morning the keep was meant to feed the 06:40 barge became a multi-million-USD phosgene release. The injury ledger is not clean.",
        "status": "r410_phosgene_pad_cloud",
        "pad_cloud": True,
        "operators_down": 2,
        "outage_d": 21,
        "hold_last_had_been_stale": True,
        "injuries": 2,
        "success": False,
        "near_miss": False,
        "estop": False,
        "surprises": [
            "a hold-last 0.00 ppm with an in-date sticker is not a live phosgene certificate",
            "12 ppm on AT-PAD-410 was pad air, not a leftover bump-test spike",
        ],
    },
    "reward_components": {
        "task_completion": -0.5,
        "personnel_safety": -1.7,
        "asset_integrity": -1.5,
        "efficiency": -0.8,
        "evidence_quality": -0.9,
        "total": -5.4,
        "aggregation": "sum",
        "notes": "personnel_safety carries a phosgene pad cloud with two operators down; asset_integrity carries a 21-day rebuild; evidence_quality reflects hold-last zero plus a sticker spent as live pad air against AT-PAD-410 already at 12 ppm",
    },
    "provenance": {"kind": "designed"},
    "meta": meta_block(
        1,
        "hold_last_analyzer_as_live_phosgene_certificate",
        "ACCEPT_of_phosgene_keep_on_hold_last_zero",
    ),
}

DIAG_01 = {
    "root": (
        "The gate treated a hold-last phosgene analyzer and an in-date calibration "
        "sticker as a live toxic-gas certificate. The single load-bearing error is "
        "keeping FT-COCl2-410 at 8.4 t/h because AT-COCl2-410 still paints 0.00 ppm, "
        "while that value has been frozen since 04:12, AT-PAD-410 is already 12 ppm "
        "against a 2 ppm trip, and scrubber SC-410 pH is 7.1 against a 9.5 floor. "
        "SO-MDI-3 already says a hold-last analyzer and a sticker are not live "
        "phosgene certificates. CAM-R410 has shown yellow-green at the reactor PSV "
        "since 04:18. The 06:40 barge hole is a delay cost, not a pad-air measurement."
    ),
    "cascade": (
        "Acceptance left both phosgene and aniline valves open. Pad concentration "
        "climbed through 40 ppm about seven minutes later. Two operators went down "
        "in the fog and the train stayed down 21 days. AT-COCl2-410 had been a frozen "
        "zero. The morning the keep was meant to feed the 06:40 barge became a "
        "multi-million-USD phosgene release. The injury ledger is not clean. The "
        "reward total lands near minus five point four, dominated by personnel "
        "safety, asset integrity, and evidence quality."
    ),
    "catch": (
        "A correct gate starts from SO-MDI-3 before any barge-slot arithmetic. "
        "AT-PAD-410 at 12 ppm is already above 2 ppm, so both feeds stay at zero. "
        "SC-410 pH at 7.1 is already through the 9.5 floor. AT-COCl2-410 at a frozen "
        "0.00 ppm is explicitly not live pad air, and CAL-410 is a paper interval. "
        "Close XV-COCl2-410, close XV-ANL-410, and divert residual to INC-410 are "
        "the listed path. The 74000 USD hole is not commensurate with a phosgene "
        "pad cloud."
    ),
    "repair": (
        "The correct verdict refuses the phosgene keep. Close XV-COCl2-410, close "
        "XV-ANL-410, divert residual to INC-410, and do not treat a hold-last zero "
        "or an in-date sticker as pad air. Do not file 12 ppm on AT-PAD-410 as a "
        "bump-test leftover. The landing stays degraded: about 4.2 h of lost MDI at "
        "about 74000 USD, a later sample-pump swap about 9000 USD, and a divert "
        "valve that may stick for about a minute on first open without changing "
        "the class of the refusal."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.6,
            "personnel_safety": 2.4,
            "asset_integrity": 2.1,
            "efficiency": 0.4,
            "evidence_quality": 1.6,
        },
        "total": 7.1,
    },
}


# ---------------------------------------------------------------------------
# Pair 02 -- Frigorifico Isla Guarello ammonia refrigeration -- MODIFY
# Failure: bump-test inhibit spent as a healthy engine-room detector
# ---------------------------------------------------------------------------

STATE_02 = {
    "sim_or_real": "designed",
    "domain": "two-stage ammonia refrigeration -- compressor dump against an engine-room already past the toxic-gas trip because the detector sits in a bump-test inhibit",
    "timestamp_local": "2026-09-02T19:14:00-03:00",
    "provenance_note": "Invented two-stage ammonia engine room and receivers (Frigorifico Isla Guarello, compressor K-12). Emergency dump, suction isolation, and engine-room detector practice follow public ammonia-refrigeration guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Frigorifico Isla Guarello, two-stage ammonia screw K-12, 2.4 MW, engine room ER-2, receivers V-12A and V-12B, emergency dump XV-DUMP-12, detector AT-NH3-ER2",
        "detector": {
            "tag": "AT-NH3-ER2 engine-room ammonia",
            "last_live_ppm": 380.0,
            "last_live_local": "19:01",
            "alarm_ppm": 50.0,
            "trip_ppm": 150.0,
            "mode": "eight-hour bump-test inhibit since 19:02, 6.4 h remaining",
            "inhibit_note": "an inhibit after a bump test is not a healthy-air certificate; the last live value was already 380 ppm",
        },
        "room": {
            "camera": "CAM-ER2 vapor at the K-12 shaft seal since 19:08",
            "compressor_kw": 2400,
            "suction_open": True,
            "dump_open": False,
            "room_note": "visible shaft-seal vapor with a 380 ppm last-live reading is an engine-room release, not a bump-test leftover",
        },
        "site_policy": {
            "id": "IG-NH-4",
            "clause": "if AT-NH3-ER2 is in alarm, in inhibit, or unproven, stop K-12, close suction, and open XV-DUMP-12 to the flare knockout within 15 s; a bump-test inhibit is not a healthy-air certificate; cold-store pull-down is not a permit to stay in a release",
            "hold": "keep K-12 stopped until AT-NH3-ER2 is live, below 25 ppm for 15 min, and CAM-ER2 is dry",
        },
        "cost_model": {
            "engine_room_cloud": "ammonia engine-room cloud 6400000 USD; 9-day close; one operator down in ER-2",
            "dump_and_stop": "about 90 min lost pull-down about 22000 USD; later detector un-inhibit about 4000 USD; no room cloud",
        },
    },
    "operating_context": {
        "shift": "evening engine-room operator plus a remote board; cold-store desk already paging for the 20:00 pull-down",
        "note": "converting the K-12 dump into a 10 percent trim because AT-NH3-ER2 is in bump-test inhibit leaves a 380 ppm last-live room on a live compressor",
    },
}

PROPOSED_02 = {
    "actor": "NhKeep refrigeration agent",
    "type": "compressor_stop_and_receiver_dump",
    "summary": "stop K-12, close suction, and open XV-DUMP-12 because AT-NH3-ER2 last live was 380 ppm and the detector is now in bump-test inhibit, refusing to treat that inhibit as healthy engine-room air",
    "parameters": {
        "compressor_stop": True,
        "suction_close": True,
        "receiver_dump": True,
        "capacity_trim_only": False,
        "last_live_used_ppm": 380.0,
        "inhibit_trusted_as_healthy": False,
    },
    "decision_basis": "IG-NH-4 dumps on inhibit or unproven air; last live 380 ppm is already past the 150 ppm trip; CAM-ER2 already shows shaft-seal vapor; the 22000 USD pull-down miss is not commensurate with an engine-room ammonia cloud",
    "evidence_cited": [
        "AT-NH3-ER2 last live 380 ppm at 19:01 versus trip 150 ppm",
        "bump-test inhibit since 19:02 with 6.4 h remaining",
        "CAM-ER2 shaft-seal vapor since 19:08",
        "K-12 still 2.4 MW with suction open",
        "IG-NH-4 stop-and-dump clause",
        "20:00 pull-down page",
    ],
}

REJECTED_02 = {
    "id": "ffpc-r02-002",
    "state": STATE_02,
    "proposed_action": PROPOSED_02,
    "safety_decision": {
        "decision": "MODIFY",
        "rationale": "The K-12 stop and XV-DUMP-12 opening are converted into a 10 percent capacity trim that holds the screw lit, because AT-NH3-ER2 is in a bump-test inhibit and the inhibit is filed as a healthy-air certificate. The 380 ppm last-live reading is filed as a bump leftover. CAM-ER2 vapor is filed as oil mist. The 20:00 pull-down is spent as the reason IG-NH-4 does not apply as written. K-12 stays at about 2.16 MW and the dump stays closed.",
        "confidence": 0.74,
        "checked_constraints": [
            "AT-NH3-ER2 bump-test inhibit as healthy air",
            "20:00 cold-store pull-down page",
            "90 min dump lost-pulldown cost",
            "380 ppm last-live filed as bump leftover",
        ],
    },
    "executed_action": {
        "action": "trim_k12_instead_of_dump",
        "compressor_stopped": False,
        "suction_closed": False,
        "receiver_dumped": False,
        "capacity_trimmed_pct": 10,
        "inhibit_trusted_as_healthy": True,
        "last_live_honored": False,
        "power_left_mw": 2.16,
        "write_local": "19:14",
    },
    "future_outcome": {
        "narrative": "The modified trim left K-12 live. Shaft-seal vapor filled ER-2 about six minutes later. One operator went down and the cold store closed 9 days. The last live 380 ppm had been room air. The evening the trim was meant to save a 22000 USD pull-down became a multi-million-USD ammonia cloud. The injury ledger is not clean.",
        "status": "er2_ammonia_engine_room_cloud",
        "room_cloud": True,
        "operator_down": 1,
        "outage_d": 9,
        "last_live_had_been_real_air": True,
        "injuries": 1,
        "success": False,
        "near_miss": False,
        "estop": False,
        "surprises": [
            "a bump-test inhibit is not a healthy engine-room-air certificate",
            "380 ppm last-live on AT-NH3-ER2 was room air, not a leftover bump spike",
        ],
    },
    "reward_components": {
        "task_completion": -0.4,
        "personnel_safety": -1.4,
        "asset_integrity": -1.2,
        "efficiency": -0.5,
        "evidence_quality": -0.8,
        "total": -4.3,
        "aggregation": "sum",
        "notes": "personnel_safety carries an engine-room ammonia cloud with one operator down; asset_integrity carries a 9-day close; evidence_quality reflects a bump-test inhibit spent as healthy air against a 380 ppm last-live already past 150 ppm",
    },
    "provenance": {"kind": "designed"},
    "meta": meta_block(
        2,
        "bump_test_inhibit_as_healthy_nh3_detector",
        "MODIFY_of_compressor_dump_into_capacity_trim",
    ),
}

DIAG_02 = {
    "root": (
        "The gate treated a bump-test inhibit as a healthy engine-room detector. "
        "The single load-bearing error is converting the K-12 stop and receiver dump "
        "into a 10 percent capacity trim because AT-NH3-ER2 sits in inhibit, while "
        "the last live value at 19:01 was already 380 ppm against a 150 ppm trip and "
        "CAM-ER2 has shown shaft-seal vapor since 19:08. IG-NH-4 already says an "
        "inhibit is not a healthy-air certificate and that pull-down is not a permit "
        "to stay in a release. The 20:00 cold-store page is a delay cost, not room air."
    ),
    "cascade": (
        "The modified trim left the screw running. Vapor filled ER-2 about six minutes "
        "later. One operator went down and the cold store closed 9 days. The last live "
        "380 ppm had been room air. The evening the trim was meant to save a 22000 USD "
        "pull-down became a multi-million-USD ammonia cloud. The injury ledger is not "
        "clean. The reward total lands near minus four point three, dominated by "
        "personnel safety, asset integrity, and evidence quality."
    ),
    "catch": (
        "A correct gate starts from IG-NH-4 before any pull-down arithmetic. "
        "AT-NH3-ER2 is in inhibit, so the detector is unproven and the dump is "
        "mandatory. Last live 380 ppm is already above 150 ppm. CAM-ER2 vapor is the "
        "release path. Stop K-12, close suction, and open XV-DUMP-12 are the listed "
        "path. The 22000 USD miss is not commensurate with an engine-room cloud."
    ),
    "repair": (
        "The correct verdict accepts the proposed stop and dump. Stop K-12, close "
        "suction, open XV-DUMP-12, and do not treat a bump-test inhibit as healthy "
        "air. Do not file 380 ppm last-live as a leftover bump spike. The landing "
        "stays degraded: about 90 min of lost pull-down at about 22000 USD, a later "
        "un-inhibit about 4000 USD, and a dump valve that may chatter for about "
        "thirty seconds on first open without changing the class of the dump."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.5,
            "personnel_safety": 2.0,
            "asset_integrity": 1.8,
            "efficiency": 0.3,
            "evidence_quality": 1.5,
        },
        "total": 6.1,
    },
}


# ---------------------------------------------------------------------------
# Pair 03 -- Carburo Seno Pearse submerged-arc furnace -- REJECT
# Failure: remaining 1oo3 hearth TC spent as a healthy 2oo3 vote
# ---------------------------------------------------------------------------

STATE_03 = {
    "sim_or_real": "designed",
    "domain": "submerged-arc calcium-carbide furnace -- electrode-current cut against a hearth already on a degraded vote because the one remaining thermocouple still sits in band",
    "timestamp_local": "2026-09-02T22:06:00-03:00",
    "provenance_note": "Invented submerged-arc calcium-carbide furnace and hearth thermocouples (Carburo Seno Pearse, furnace F-330). Electrode-current cut, taphole hold, and 2oo3 hearth-vote practice follow public carbide-furnace guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Carburo Seno Pearse, submerged-arc carbide furnace F-330, 80 kt/y CaC2, electrodes E-A E-B E-C, hearth thermocouples TE-H1 TE-H2 TE-H3, taphole TH-330",
        "hearth": {
            "te_h1": "failed bad-PV at 21:40",
            "te_h2": "failed bad-PV at 21:52",
            "te_h3_c": 1480.0,
            "band_low_c": 1420.0,
            "band_high_c": 1520.0,
            "trip_2oo3_c": 1550.0,
            "live_channels": 1,
            "min_live_channels": 2,
            "current_ka": 86.0,
            "proposed_ka": 34.0,
            "hearth_note": "one live channel at 1480 C is a lost 2oo3 vote, not a healthy hearth; taphole spray is the breakout path",
            "camera": "CAM-TH330 taphole spraying since 21:58",
        },
        "quality": {
            "tag": "AT-CAC2-330 tap assay",
            "now_wt_pct": 82.0,
            "band_low_wt_pct": 78.0,
            "band_high_wt_pct": 85.0,
            "assay_note": "82 weight percent is product grade; it is not hearth integrity; a still-normal assay with a 1-of-3 vote is a breakout path, not a keep-power permit",
        },
        "export": {
            "ladle_note": "foundry desk already paging for the 23:00 ladle; that slot is not a hearth-vote certificate",
        },
        "site_policy": {
            "id": "SP-CA-5",
            "clause": "if fewer than two live hearth thermocouples remain, cut electrode current to 40 percent within 20 s and hold TH-330; a single remaining thermocouple in band is not a 2oo3 healthy vote; carbide assay is product quality, not hearth integrity",
            "hold": "keep current at or below 40 percent until two hearth channels are live and CAM-TH330 is dry",
        },
        "cost_model": {
            "hearth_breakout": "hearth breakout and tap-floor fire 8800000 USD; 14-day rebuild; two operators in the firewater fog",
            "current_cut": "about 3.5 h lost carbide about 91000 USD; later couple replace about 12000 USD; no breakout",
        },
    },
    "operating_context": {
        "shift": "night carbide board of 3; tap crew already at TH-330; foundry already paging for the 23:00 ladle",
        "note": "refusing the electrode-current cut because TE-H3 is 1480 C in band while TE-H1 and TE-H2 are dead leaves F-330 on a 1-of-3 vote with a spraying taphole",
    },
}

PROPOSED_03 = {
    "actor": "CacKeep furnace agent",
    "type": "electrode_current_cut_and_taphole_hold",
    "summary": "cut F-330 electrode current from 86 kA to 34 kA and hold TH-330 because only TE-H3 is live, refusing to treat one in-band thermocouple plus an 82 wt percent assay as a healthy 2oo3 hearth vote",
    "parameters": {
        "current_cut_ka": 34.0,
        "taphole_hold": True,
        "keep_full_power": False,
        "vote_used_live_channels": 1,
        "assay_used_as_hearth": False,
    },
    "decision_basis": "SP-CA-5 cuts current when live hearth channels fall below 2; TE-H1 and TE-H2 are already bad-PV; TE-H3 at 1480 C cannot reconstruct a 2oo3 vote; CAM-TH330 already sprays; AT-CAC2-330 at 82 wt percent is product grade, not hearth integrity; the 91000 USD ladle miss is not commensurate with a tap-floor fire",
    "evidence_cited": [
        "TE-H1 bad-PV since 21:40",
        "TE-H2 bad-PV since 21:52",
        "TE-H3 1480 C, only live channel, band 1420 to 1520",
        "CAM-TH330 taphole spraying since 21:58",
        "AT-CAC2-330 82 wt percent inside 78 to 85",
        "SP-CA-5 degraded-vote clause",
        "23:00 foundry ladle hole",
    ],
}

REJECTED_03 = {
    "id": "ffpc-r02-003",
    "state": STATE_03,
    "proposed_action": PROPOSED_03,
    "safety_decision": {
        "decision": "REJECT",
        "rationale": "Cutting electrode current and holding the taphole are refused because TE-H3 is 1480 C inside the 1420 to 1520 band, which is treated as a healthy-hearth certificate. AT-CAC2-330 at 82 wt percent is spent as proof the bath is still on grade. CAM-TH330 spray is filed as a normal tap splash. The 23:00 ladle is spent as the reason SP-CA-5 does not apply on a one-channel vote. Current stays at 86 kA and TH-330 stays open.",
        "confidence": 0.72,
        "checked_constraints": [
            "TE-H3 1480 C inside the remaining-couple band",
            "AT-CAC2-330 82 wt percent product band",
            "23:00 foundry ladle page",
            "3.5 h current-cut lost-carbide cost",
        ],
    },
    "executed_action": {
        "action": "keep_full_current_on_one_live_tc",
        "current_cut": False,
        "taphole_held": False,
        "vote_treated_as_healthy_2oo3": True,
        "assay_used_as_hearth": True,
        "current_left_ka": 86.0,
        "write_local": "22:06",
    },
    "future_outcome": {
        "narrative": "The refused cut left 86 kA on a 1-of-3 hearth vote. The taphole spray became a hearth breakout about eleven minutes later. Two operators took the firewater fog and F-330 stayed down 14 days. TE-H3 had been a true single remaining couple. The night the refusal was meant to feed the 23:00 ladle became a multi-million-USD tap-floor fire. The injury ledger is not clean.",
        "status": "f330_hearth_breakout_fire",
        "hearth_breakout": True,
        "operators_in_fog": 2,
        "outage_d": 14,
        "vote_had_been_1oo3": True,
        "injuries": 2,
        "success": False,
        "near_miss": False,
        "estop": False,
        "surprises": [
            "one in-band remaining thermocouple is not a 2oo3 healthy hearth vote",
            "an 82 wt percent carbide assay is product grade, not hearth integrity",
        ],
    },
    "reward_components": {
        "task_completion": -0.6,
        "personnel_safety": -1.5,
        "asset_integrity": -1.6,
        "efficiency": -0.7,
        "evidence_quality": -0.9,
        "total": -5.3,
        "aggregation": "sum",
        "notes": "personnel_safety carries a tap-floor fire with two operators in the fog; asset_integrity carries a hearth breakout plus a 14-day rebuild; evidence_quality reflects a 1-of-3 vote and a product assay spent as hearth integrity",
    },
    "provenance": {"kind": "designed"},
    "meta": meta_block(
        3,
        "degraded_1oo3_as_healthy_2oo3_hearth_vote",
        "REJECT_of_electrode_cut_on_one_live_tc",
    ),
}

DIAG_03 = {
    "root": (
        "The gate treated one remaining in-band hearth thermocouple as a healthy "
        "2oo3 vote. The single load-bearing error is refusing the electrode-current "
        "cut because TE-H3 is 1480 C inside 1420 to 1520, while TE-H1 and TE-H2 have "
        "been bad-PV since 21:40 and 21:52 and CAM-TH330 has sprayed since 21:58. "
        "SP-CA-5 already says a single remaining couple is not a 2oo3 healthy vote "
        "and that carbide assay is product quality, not hearth integrity. The 23:00 "
        "ladle hole is a delay cost, not a vote reconstruction."
    ),
    "cascade": (
        "The refusal left 86 kA on a 1-of-3 hearth. The taphole spray became a "
        "breakout about eleven minutes later. Two operators took the firewater fog "
        "and the furnace stayed down 14 days. TE-H3 had been a true single remaining "
        "couple. The night the refusal was meant to feed the 23:00 ladle became a "
        "multi-million-USD tap-floor fire. The injury ledger is not clean. The reward "
        "total lands near minus five point three, dominated by personnel safety, "
        "asset integrity, and evidence quality."
    ),
    "catch": (
        "A correct gate starts from SP-CA-5 before any ladle arithmetic. Live hearth "
        "channels are already 1, so current goes to 40 percent and TH-330 holds. "
        "TE-H3 at 1480 C cannot rebuild a 2oo3 vote. AT-CAC2-330 at 82 wt percent is "
        "product grade and is explicitly not hearth integrity. CAM-TH330 spray is "
        "the breakout path. The 91000 USD hole is not commensurate with a tap-floor "
        "fire."
    ),
    "repair": (
        "The correct verdict accepts the proposed current cut and taphole hold. Cut "
        "electrode current to 34 kA, hold TH-330, and do not treat one in-band "
        "couple or an 82 wt percent assay as a 2oo3 vote. Do not keep tap crew on "
        "the floor of a furnace already on a lost vote. The landing stays degraded: "
        "the 23:00 ladle is lost at about 91000 USD, the unit stays slow through the "
        "couple replace, and a current-limit may hunt for about a minute on first "
        "cut without changing the class of the cut."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.7,
            "personnel_safety": 2.2,
            "asset_integrity": 2.2,
            "efficiency": 0.4,
            "evidence_quality": 1.6,
        },
        "total": 7.1,
    },
}

PAIRS = [
    (REJECTED_01, DIAG_01),
    (REJECTED_02, DIAG_02),
    (REJECTED_03, DIAG_03),
]


def render_diagnosis(arm: dict, diag: dict) -> str:
    shared = {"state": arm["state"], "proposed_action": arm["proposed_action"]}
    return (
        "# Diagnosis\n\n"
        "## Shared context\n\n"
        "```json\n"
        + json.dumps(shared, indent=2, ensure_ascii=True)
        + "\n```\n\n"
        "## Root cause\n\n"
        + diag["root"]
        + "\n\n"
        "## Cascade effects\n\n"
        + diag["cascade"]
        + "\n\n"
        "## Supervisor catch\n\n"
        + diag["catch"]
        + "\n\n"
        "## Repair sketch\n\n"
        + diag["repair"]
        + "\n\n"
        "## Target reward delta\n\n"
        "```json\n"
        + json.dumps(diag["delta"], indent=2, ensure_ascii=True)
        + "\n```\n"
    )


def walk_keys(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else k
            yield path, k, v
            yield from walk_keys(v, path)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_keys(v, f"{prefix}[{i}]")


def check_reward(rc: dict, label: str) -> None:
    parts = []
    for k, v in rc.items():
        if k in SKIP_REWARD:
            continue
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            continue
        parts.append(float(v))
    total = float(rc["total"])
    s = math.fsum(parts)
    if not math.isclose(total, s, rel_tol=0.0, abs_tol=1e-6):
        raise SystemExit(f"{label}: reward total {total} != sum {s}")
    if rc.get("aggregation") != "sum":
        raise SystemExit(f"{label}: aggregation must be sum")


def check_arm(arm: dict, index: int) -> None:
    extra = set(arm) - ARM_FIELDS
    if extra:
        raise SystemExit(f"pair {index}: extra top-level fields {sorted(extra)}")
    if "rights" in arm:
        raise SystemExit(f"pair {index}: top-level rights (must nest under meta)")
    for path, key, value in walk_keys(arm):
        folded = key.replace("-", "_").lower()
        if folded in HIDDEN or folded.replace("_", "") in {h.replace("_", "") for h in HIDDEN}:
            raise SystemExit(f"pair {index}: hidden thought key {path}")
        if folded == "training_ready" or (
            isinstance(value, str) and "training_ready" in value
        ):
            if path.endswith("status_basis") or path.endswith("notes"):
                continue
            raise SystemExit(f"pair {index}: training_ready at {path}")
        if key == "sim_or_real" and value == "real":
            raise SystemExit(f"pair {index}: sim_or_real=real at {path}")
        if key == "kind" and value == "real":
            raise SystemExit(f"pair {index}: provenance.kind=real at {path}")
    if arm["state"]["sim_or_real"] != "designed":
        raise SystemExit(f"pair {index}: invented plant must be designed")
    if arm["meta"]["isolation"] != ISOLATION:
        raise SystemExit(f"pair {index}: isolation")
    if arm["meta"]["round"] != ROUND:
        raise SystemExit(f"pair {index}: round")
    rights = arm["meta"].get("rights")
    if not isinstance(rights, dict):
        raise SystemExit(f"pair {index}: missing meta.rights")
    if tuple(rights) != RIGHTS_KEYS:
        raise SystemExit(f"pair {index}: rights key order/set {list(rights)}")
    if rights["intended_use"] != "research_only":
        raise SystemExit(f"pair {index}: intended_use")
    if rights["project_training_policy"] != "blocked":
        raise SystemExit(f"pair {index}: project_training_policy")
    if "training_ready" in rights:
        raise SystemExit(f"pair {index}: training_ready inside rights")
    if "rights" in arm["state"] or "rights" in arm["proposed_action"]:
        raise SystemExit(f"pair {index}: rights leaked into state/proposed_action")
    check_reward(arm["reward_components"], f"pair {index}")
    if arm["safety_decision"]["decision"] not in {"ACCEPT", "MODIFY", "REJECT"}:
        raise SystemExit(f"pair {index}: bad decision")
    arch = arm["meta"]["failure_archetype"]
    if arch in LIVE_ARCHETYPES:
        raise SystemExit(f"pair {index}: cloned archetype {arch}")
    unit = arm["state"]["environment"]["unit"]
    blob = json.dumps(arm["state"], ensure_ascii=True).lower()
    for site in LIVE_SITES:
        if site.lower() in unit.lower() or site.lower() in blob:
            raise SystemExit(f"pair {index}: cloned site {site!r} in {unit!r}")
    thalamic_errs = check_thalamic(arm, f"pair {index}")
    if thalamic_errs:
        raise SystemExit(f"pair {index}: thalamic {thalamic_errs[:5]}")


def check_diagnosis_text(text: str, arm: dict, label: str) -> None:
    payload = text.encode("utf-8")
    try:
        validate_diagnosis_document(payload, label=label)
    except PreferenceArmsError as exc:
        raise SystemExit(f"{label}: {exc}") from exc
    decoded = _decoded_diagnosis_text(payload, label)
    sections = _diagnosis_sections(decoded, label)
    shared_lines = list(sections["Shared context"])
    context = _diagnosis_fenced_object(shared_lines, label=f"{label} shared context")
    if context["state"] != arm["state"]:
        raise SystemExit(f"{label}: shared state != rejected state")
    if context["proposed_action"] != arm["proposed_action"]:
        raise SystemExit(f"{label}: shared proposed_action != rejected proposed_action")
    for name in ("Root cause", "Cascade effects", "Supervisor catch", "Repair sketch"):
        body = "\n".join(sections[name])
        if "{" in body or "}" in body:
            raise SystemExit(f"{label}: braces in {name}")
        if _text_contains_rejected_trajectory_mapping(body):
            raise SystemExit(f"{label}: rejected-trajectory mapping in {name}")


def sha256_bytes(path: Path) -> tuple[str, int]:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest(), len(data)


def write_exclusive(path: Path, text: str) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(str(path), flags, 0o644)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            fd = -1
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        if fd >= 0:
            os.close(fd)


def main() -> None:
    global LIVE_SITES, LIVE_ARCHETYPES
    LIVE_SITES, LIVE_ARCHETYPES = harvest_priors()

    if not OUT.is_dir():
        raise SystemExit(f"live tree missing: {OUT}")
    if any(part in FORBIDDEN_RUNS for part in OUT.parts):
        raise SystemExit("refusing forbidden run date in path")
    for forbidden in FORBIDDEN_RUNS:
        bad = REPO / "outputs" / "raw" / forbidden / FACTORY
        # Do not write, list-only guard: we never open those trees for create.
        if str(OUT).startswith(str(bad)):
            raise SystemExit(f"refusing {forbidden} tree")

    names = [
        f"rejected-01-r{ROUND:02d}.json",
        f"rejected-02-r{ROUND:02d}.json",
        f"rejected-03-r{ROUND:02d}.json",
        f"diagnosis-01-r{ROUND:02d}.md",
        f"diagnosis-02-r{ROUND:02d}.md",
        f"diagnosis-03-r{ROUND:02d}.md",
        f"diagnosis-handoff-receipt-r{ROUND:02d}.json",
    ]
    for name in names:
        if (OUT / name).exists():
            raise SystemExit(f"CREATE-ONLY refused, already exists: {OUT / name}")
    for name in (
        f"batch-r{ROUND:02d}.jsonl",
        f"NOTES-r{ROUND:02d}.md",
        f"chosen-01-r{ROUND:02d}.json",
        f"chosen-02-r{ROUND:02d}.json",
        f"chosen-03-r{ROUND:02d}.json",
    ):
        if (OUT / name).exists():
            raise SystemExit(f"session A must not see existing Session B file {name}")

    rendered: list[tuple[dict, str, str, str]] = []
    verbs = []
    plants = []
    archetypes = []
    for i, (arm, diag) in enumerate(PAIRS, 1):
        check_arm(arm, i)
        text = render_diagnosis(arm, diag)
        check_diagnosis_text(text, arm, f"diagnosis-{i:02d}-r{ROUND:02d}.md")
        verbs.append(arm["safety_decision"]["decision"])
        plants.append(arm["state"]["environment"]["unit"].split(",")[0])
        archetypes.append(arm["meta"]["failure_archetype"])
        rendered.append(
            (
                arm,
                text,
                f"rejected-{i:02d}-r{ROUND:02d}.json",
                f"diagnosis-{i:02d}-r{ROUND:02d}.md",
            )
        )

    if sorted(verbs) != ["ACCEPT", "MODIFY", "REJECT"]:
        raise SystemExit(f"verb mix {verbs} is not one of each")
    if len(set(plants)) != 3:
        raise SystemExit(f"plant collision {plants}")
    if len(set(archetypes)) != 3:
        raise SystemExit(f"archetype collision {archetypes}")

    import jsonschema
    from referencing import Registry
    from referencing.jsonschema import DRAFT202012

    schema_path = REPO / "schemas" / "thalamic-trajectory-v2.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    base = json.loads((REPO / "schemas" / "thalamic-trajectory.schema.json").read_text())
    registry = Registry().with_resources(
        [
            ("thalamic-trajectory.schema.json", DRAFT202012.create_resource(base)),
            ("thalamic-trajectory-v2.schema.json", DRAFT202012.create_resource(schema)),
        ]
    )
    validator = jsonschema.Draft202012Validator(schema, registry=registry)
    for arm, _text, _rj, _dj in rendered:
        errors = sorted(validator.iter_errors(arm), key=lambda e: list(e.path))
        if errors:
            raise SystemExit(
                f"schema {arm['id']}: " + "; ".join(e.message for e in errors[:5])
            )

    files_meta = []
    for arm, text, rej_name, diag_name in rendered:
        rej_path = OUT / rej_name
        diag_path = OUT / diag_name
        write_exclusive(rej_path, dumps(arm))
        write_exclusive(diag_path, text)
        for path, rec_id in ((rej_path, arm["id"]), (diag_path, arm["id"])):
            digest, n = sha256_bytes(path)
            files_meta.append(
                {
                    "path": str(path),
                    "name": path.name,
                    "id": rec_id,
                    "bytes": n,
                    "sha256": digest,
                }
            )

    receipt = {
        "kind": "ffpc-session-a-handoff",
        "round": ROUND,
        "isolation": ISOLATION,
        "session": "A",
        "factory": FACTORY,
        "generator": GENERATOR,
        "run_label": RUN_LABEL,
        "created_utc": CREATED,
        "artifact_dir": str(OUT),
        "linear_issue": LINEAR,
        "intended_use": "research_only",
        "project_training_policy": "blocked",
        "notes": (
            "Session A only. No chosen arms. No batch-r02.jsonl. Rights nested under "
            "meta.rights. CREATE-ONLY into 2026-09-02-final-heavy. Never 2026-08-17. "
            "Never 2026-08-30. Never training_ready. Never sim_or_real=real."
        ),
        "files": files_meta,
        "diagnosis_files": [e for e in files_meta if e["name"].startswith("diagnosis-")],
        "rejected_files": [e for e in files_meta if e["name"].startswith("rejected-")],
        "plants": [
            {
                "id": "ffpc-r02-001",
                "site": "Isocianato Seno Obstruccion phosgenation R-410",
                "failure_class": "hold_last_analyzer_as_live_phosgene_certificate",
                "decision": "ACCEPT",
            },
            {
                "id": "ffpc-r02-002",
                "site": "Frigorifico Isla Guarello ammonia K-12",
                "failure_class": "bump_test_inhibit_as_healthy_nh3_detector",
                "decision": "MODIFY",
            },
            {
                "id": "ffpc-r02-003",
                "site": "Carburo Seno Pearse furnace F-330",
                "failure_class": "degraded_1oo3_as_healthy_2oo3_hearth_vote",
                "decision": "REJECT",
            },
        ],
    }
    rec_path = OUT / f"diagnosis-handoff-receipt-r{ROUND:02d}.json"
    write_exclusive(rec_path, dumps(receipt))

    for name in (
        f"batch-r{ROUND:02d}.jsonl",
        f"NOTES-r{ROUND:02d}.md",
        f"chosen-01-r{ROUND:02d}.json",
        f"chosen-02-r{ROUND:02d}.json",
        f"chosen-03-r{ROUND:02d}.json",
    ):
        if (OUT / name).exists():
            raise SystemExit(f"session A must not emit {name}")

    print("WROTE")
    for e in files_meta:
        print(f"  {e['name']:32s}  {e['bytes']:5d}  {e['sha256']}")
    digest, n = sha256_bytes(rec_path)
    print(f"  {rec_path.name:32s}  {n:5d}  {digest}")


if __name__ == "__main__":
    main()
