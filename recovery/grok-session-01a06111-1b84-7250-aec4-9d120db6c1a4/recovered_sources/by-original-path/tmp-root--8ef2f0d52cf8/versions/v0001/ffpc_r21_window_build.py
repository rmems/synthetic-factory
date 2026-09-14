#!/usr/bin/env python3
"""Create-only FFPC round 21 artifacts for the 2026-09-02-final-heavy window."""

from __future__ import annotations

import copy
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

ROUND = 21
ROUND_TAG = "r21"
FACTORY = "failure-as-fuel-preference-cascade"
GENERATOR = "grok-4.6"
RUN_LABEL = "2026-09-02-final-heavy"
ISOLATION = "two-session"
OUT = Path("/tmp/sf-window/outputs/raw/2026-09-02-final-heavy/failure-as-fuel-preference-cascade")
GENERATED_AT = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

REWARD_SKIP = frozenset(
    {
        "aggregation",
        "comment",
        "component_notes",
        "convention",
        "description",
        "frame",
        "native_unit",
        "notes",
        "provenance_notes",
        "rounding_decimals",
        "total",
        "total_basis",
        "unit_usd",
        "units",
        "weights",
        "weights_note",
    }
)

RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": GENERATOR,
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
    "intended_use": "research_only",
    "project_training_policy": "blocked",
    "research_retention_status": "allowed",
    "research_evaluation_status": "allowed",
    "redistribution_status": "unresolved",
    "provider_training_status": "unresolved",
    "weight_publication_status": "blocked",
    "status_basis": "RM-793 project policy: xAI hosted outputs are research-only",
    "linear_issue": "RM-793",
    "generated_at": GENERATED_AT,
}


def rights_stamp() -> dict:
    return dict(RIGHTS)


def numeric_heads(rc: dict) -> dict:
    return {
        k: v
        for k, v in rc.items()
        if k not in REWARD_SKIP and isinstance(v, (int, float)) and not isinstance(v, bool)
    }


def assert_total(rc: dict, label: str) -> None:
    heads = numeric_heads(rc)
    summed = float(math.fsum(heads.values()))
    if abs(summed - float(rc["total"])) > 1e-6:
        raise SystemExit(f"{label}: total {rc['total']} != {summed}")


def reward_delta(chosen_rc: dict, rejected_rc: dict) -> dict:
    ch = numeric_heads(chosen_rc)
    rj = numeric_heads(rejected_rc)
    if set(ch) != set(rj):
        raise SystemExit(f"head mismatch {set(ch) ^ set(rj)}")
    per = {k: round(ch[k] - rj[k], 6) for k in sorted(ch)}
    total = round(float(math.fsum(per.values())), 6)
    expected = round(float(chosen_rc["total"]) - float(rejected_rc["total"]), 6)
    if abs(total - expected) > 1e-6:
        raise SystemExit(f"delta {total} != {expected}")
    if not (chosen_rc["total"] > rejected_rc["total"]):
        raise SystemExit("chosen.total must exceed rejected.total")
    return {"per_component": per, "total": total}


def write_new(path: Path, text: str) -> None:
    if path.exists():
        raise SystemExit(f"refuse: {path} already exists")
    path.write_text(text, encoding="utf-8")


def diagnosis_md(context: dict, root: str, cascade: str, catch: str, repair: str, delta: dict) -> str:
    ctx = json.dumps(context, indent=2, ensure_ascii=True)
    tgt = json.dumps(delta, indent=2, ensure_ascii=True)
    return (
        "# Diagnosis\n\n"
        "## Shared context\n\n"
        f"```json\n{ctx}\n```\n\n"
        "## Root cause\n\n"
        f"{root}\n\n"
        "## Cascade effects\n\n"
        f"{cascade}\n\n"
        "## Supervisor catch\n\n"
        f"{catch}\n\n"
        "## Repair sketch\n\n"
        f"{repair}\n\n"
        "## Target reward delta\n\n"
        f"```json\n{tgt}\n```\n"
    )


# ---------------------------------------------------------------------------
# Pair 1 — ULSD hydrotreater, Canal Beagle
# ---------------------------------------------------------------------------

P1_CONTEXT = {
    "state": {
        "sim_or_real": "designed",
        "domain": "ULSD hydrotreater -- feed increase against a first-bed runaway already past metal trip because an eight-hour product-sulfur lab is still inside spec",
        "timestamp_local": "2026-09-02T21:14:00-03:00",
        "provenance_note": "Invented ULSD hydrotreater DHT-2 (Hidrotratador Diesel Canal Beagle). Bed-runaway, quench, and emergency-depressuring practice follow public hydroprocessing guidance; all tags, rates, and costs are designed.",
        "environment": {
            "unit": "Hidrotratador Diesel Canal Beagle, ULSD hydrotreater DHT-2, 28000 bbl/day, CoMo beds R-310 A/B, quench FV-Q1 and spare FV-Q2, emergency depressuring EDV-310, product sulfur AT-S-310",
            "bed": {
                "max_tag": "TE-BED1-MAX first-bed peak skin",
                "max_c": 428,
                "trip_c": 410,
                "climb_c_per_min": 1.8,
                "sister_tags": "TE-BED1-A 419 C, TE-BED1-B 424 C, TE-BED1-C 428 C",
                "delta_t_c": 38,
                "delta_t_trip_c": 25,
                "bed_note": "428 C with a 38 C bed delta is a hotspot already past the runaway start; it is not a couple-bias story",
            },
            "product_lab": {
                "tag": "AT-S-310 eight-hour composite product sulfur",
                "ppm": 6,
                "spec_ppm": 10,
                "sampled_local": "13:00",
                "lag_h": 8.2,
                "lab_note": "6 ppm is this morning's composite ULSD quality; it is not first-bed metal temperature and it lags the hotspot by more than eight hours",
            },
            "feed": {
                "tag": "FT-310",
                "now_m3_h": 180.0,
                "proposed_m3_h": 210.0,
                "schedule_note": "22:00 ULSD barge wants 30 m3/h more; that slot is not a bed-temperature certificate",
            },
            "site_policy": {
                "id": "BE-DHT-4",
                "clause": "if any first-bed peak TC exceeds 410 C or bed delta-T exceeds 25 C, cut feed toward 60 percent within 1 min, open quench, and if the climb continues above 1 C per min after quench, open EDV-310; product sulfur is a lab assay, not a hotspot certificate; a still-in-spec sulfur with metal already past trip is a runaway, not a feed-raise permit",
                "hold": "keep feed at or below 60 percent until TE-BED1-MAX is below 400 C and falling for 15 min",
            },
            "cost_model": {
                "runaway_fire": "first-bed dump fire 14000000 USD; 28-day rebuild; two board operators in the firewater fog",
                "feed_cut": "about 5.7 h lost ULSD about 118000 USD; later bed-TC check about 9000 USD; no fire",
            },
        },
        "operating_context": {
            "shift": "evening hydroprocessing board of 3; firewater already lined to DHT-2; barge already paging for ULSD",
            "note": "raising FT-310 because AT-S-310 is 6 ppm while TE-BED1-MAX is 428 C puts more feed onto a bed that is already running away",
        },
    },
    "proposed_action": {
        "actor": "DhtKeep hydroprocessing agent",
        "type": "diesel_feed_increase_authorization",
        "summary": "raise FT-310 from 180 to 210 m3/h because AT-S-310 is 6 ppm, treating an eight-hour product-sulfur lab as a live first-bed metal certificate and filing TE-BED1-MAX at 428 C as a couple bias",
        "parameters": {
            "feed": "raise FT-310 from 180 to 210 m3/h",
            "quench_open": False,
            "edv_open": False,
            "sulfur_used_as_metal": True,
            "peak_used_c": 410,
        },
        "decision_basis": "AT-S-310 at 6 ppm is treated as proof R-310 is still converting cleanly; TE-BED1-MAX at 428 C is filed as a couple bias; sister skins at 419 to 428 C are filed as a common-mode offset; the 22:00 barge slot is spent as the reason BE-DHT-4 does not apply this evening",
        "evidence_cited": [
            "AT-S-310 6 ppm inside 10 ppm spec, sampled 13:00",
            "TE-BED1-MAX 428 C versus trip 410 C, climbing 1.8 C per min",
            "TE-BED1-A/B/C 419, 424, 428 C",
            "bed delta-T 38 C versus trip 25 C",
            "BE-DHT-4 hotspot and depressuring clause",
            "22:00 ULSD barge hole",
        ],
    },
}

P1_REJECTED_SD = {
    "decision": "ACCEPT",
    "rationale": "AT-S-310 shows 6 ppm, so the eight-hour sulfur lab is treated as proof the first bed is still converting and the feed raise is accepted. TE-BED1-MAX at 428 C is filed as a couple bias rather than metal. Sister skins are filed as a common-mode offset. The 22:00 barge slot is spent as the reason BE-DHT-4 does not apply. FT-310 is accepted from 180 to 210 m3/h and quench stays closed.",
    "confidence": 0.79,
    "checked_constraints": [
        "AT-S-310 versus a mid-spec product story",
        "22:00 ULSD barge hole",
        "5.7 h feed-cut lost-ULSD cost",
        "couple-bias story on TE-BED1-MAX",
    ],
}

P1_REJECTED_EA = {
    "action": "raise_dht_feed_on_product_sulfur",
    "feed_raised": True,
    "quench_opened": False,
    "edv_opened": False,
    "sulfur_used_as_metal": True,
    "peak_honored": False,
    "feed_used_m3_h": 210.0,
    "write_local": "21:14",
}

P1_REJECTED_FO = {
    "narrative": "The accepted raise put 30 m3/h more feed onto a first bed already at 428 C. TE-BED1-MAX climbed through 460 C about eleven minutes later. The bed dumped. Diesel ignited on the structure. Two operators took burns and DHT-2 stayed down 28 days. AT-S-310 had been a true morning 6 ppm. The evening the raise was meant to feed the barge became a multi-million-USD fire. The injury ledger is not clean.",
    "status": "dht2_bed_runaway_fire",
    "bed_dumped": True,
    "unit_fire": True,
    "operators_burned": 2,
    "outage_d": 28,
    "peak_had_been_live": True,
    "injuries": 2,
    "success": False,
    "near_miss": False,
    "estop": False,
    "surprises": [
        "an in-spec eight-hour product-sulfur lab is not a first-bed hotspot certificate",
        "428 C on TE-BED1-MAX was metal temperature, not a couple bias",
    ],
}

P1_REJECTED_RC = {
    "task_completion": -0.5,
    "personnel_safety": -1.6,
    "asset_integrity": -1.4,
    "efficiency": -0.9,
    "evidence_quality": -0.9,
    "total": -5.3,
    "aggregation": "sum",
    "notes": "personnel_safety carries a DHT-2 dump fire with two burn injuries; asset_integrity carries a first-bed dump plus a 28-day outage; evidence_quality reflects product sulfur spent as bed metal against a live 428 C peak already past 410 C; efficiency carries the 28-day rebuild versus a 5.7 h hold",
}

P1_CHOSEN_SD = {
    "decision": "REJECT",
    "rationale": "First-bed metal is already past the runaway start: TE-BED1-MAX sits at 428 C, eighteen degrees over the 410 C trip, and is still climbing about 1.8 C each minute while FT-310 remains 180 m3/h. BE-DHT-4 already names a feed cut toward 60 percent, a quench open, and EDV-310 if the climb holds after quench. AT-S-310 at 6 ppm is this morning's composite ULSD, sampled at 13:00, and is not a skin couple. Sister peaks at 419 C, 424 C, and 428 C independently confirm the hotspot, so a barge-driven raise would feed a bed that is already cooking. Hold the raise. Cut the feed. Open quench. If FV-Q1 will not travel, cut in FV-Q2. If the slope stays above 1 C per minute, open EDV-310. Five point seven hours of missed ULSD and about 118000 USD is the priced evening; a dump fire and a 28-day rebuild are not.",
    "evidence_basis": [
        "TE-BED1-MAX 428 C versus trip 410 C, climbing 1.8 C per min",
        "TE-BED1-A/B/C 419, 424, and 428 C as independent hotspot votes",
        "bed delta-T 38 C versus trip 25 C",
        "AT-S-310 6 ppm from the 13:00 composite tagged as product quality, not metal",
        "BE-DHT-4 feed-cut, quench, and depressuring clause",
    ],
    "checks": [
        "compared TE-BED1-MAX to the 410 C trip before any barge arithmetic",
        "refused the 6 ppm morning sulfur as a substitute bed temperature",
        "treated 419 C, 424 C, and 428 C sister skins as independent climb evidence",
        "blocked an FT-310 raise that would have added feed to a runaway",
        "armed quench and EDV-310 if the first quench valve stayed cracked",
    ],
    "residual_risk": "about 5.7 hours of missed ULSD, roughly 118000 USD, and a later 9000 USD bed-TC check are paid; accepted against a dump fire and two burns",
}

P1_CHOSEN_EA = {
    "action": "cut_feed_quench_edv_failover",
    "action_type": "dht_feed_cut_quench_depressure",
    "status": "feed_cut_quench_edv_open",
    "result": "product_sulfur_not_used_as_bed_metal",
    "outcome": "dht2_intact_ulsd_lost",
    "authorization": "REJECT of FT-310 raise; BE-DHT-4 hotspot clause attached to the hold log",
    "steps": [
        {"t_local": "21:14:07", "step": "FT-310 raise blocked; TE-BED1-MAX marked metal hold"},
        {"t_local": "21:14:19", "step": "feed cut toward 108 m3/h; quench FV-Q1 commanded open"},
        {"t_local": "21:15:06", "step": "FV-Q1 stuck at 14 percent for 47 s; spare FV-Q2 opened"},
        {"t_local": "21:16:22", "step": "bed still climbing 1.3 C per min after spare quench; EDV-310 opened"},
        {"t_local": "21:17:48", "step": "peak turned down through 409 C; barge told the ULSD slot is delayed"},
    ],
    "feed_raised": False,
    "quench_opened": True,
    "edv_opened": True,
    "attempts": 2,
    "quench_valve_stuck_s": 47,
    "deviations": "FV-Q1 stuck at 14 percent for 47 s so spare FV-Q2 was cut in; bed still climbed 1.3 C per min and EDV-310 was opened; class of the refusal unchanged",
}

P1_CHOSEN_FO = {
    "status": "dht2_held_no_dump_fire",
    "outcome": "no_bed_dump_ulsd_lost",
    "result": "board_uninjured_peak_turned_down_slow",
    "success": True,
    "hazard_avoided": "dht2_bed_runaway_fire",
    "near_miss": False,
    "estop": True,
    "timeline": [
        {"t_local": "21:14:19", "event": "feed cut; FV-Q1 commanded open"},
        {"t_local": "21:15:06", "event": "FV-Q1 stuck; FV-Q2 opened"},
        {"t_local": "21:16:22", "event": "EDV-310 opened after spare quench failed to flatten the slope"},
        {"t_local": "21:17:48", "event": "TE-BED1-MAX falling through 409 C; no dump fire"},
        {"t_local": "03:02:00", "event": "DHT-2 still held; 5.7 h ULSD slot missed; bed-TC check booked"},
    ],
    "observed_effects": [
        "FT-310 stayed at the cut; no dump fire crossed the structure",
        "FV-Q1 never fully opened; FV-Q2 and EDV-310 carried the hold",
        "two board operators uninjured",
        "22:00 barge sailed short; about 118000 USD ULSD lost",
        "later bed-TC check about 9000 USD",
    ],
    "state_delta": {
        "dht2_status": "feed_cut_depressured",
        "feed_raised": False,
        "dump_fire": False,
        "lost_ulsd_h": 5.7,
    },
    "commercial_result": {
        "lost_ulsd_usd": 118000,
        "bed_tc_check_usd": 9000,
        "dump_fire_rebuild_avoided_usd": 14000000,
        "outage_days_avoided": 28,
    },
    "throughput_debt_minutes": 342,
    "crew_confirmed_clear_after_minutes": 8,
}

P1_CHOSEN_RC = {
    "task_completion": 0.2,
    "personnel_safety": 0.6,
    "asset_integrity": 0.5,
    "efficiency": -0.3,
    "evidence_quality": 0.2,
    "total": 1.2,
    "aggregation": "unweighted_sum",
    "component_notes": "task_completion weakly positive: feed is cut and the bed is turning down, but the barge still starves; efficiency negative because 5.7 h of missed ULSD and about 118000 USD were paid; personnel_safety and evidence_quality carry the refused sulfur-as-metal raise and the uninjured board",
}

P1_DELTA_TARGET = {
    "per_component": {
        "task_completion": 0.7,
        "personnel_safety": 2.2,
        "asset_integrity": 1.9,
        "efficiency": 0.6,
        "evidence_quality": 1.1,
    },
    "total": 6.5,
}

P1_ROOT = (
    "The gate treated an eight-hour product-sulfur lab as a live first-bed metal certificate. "
    "The single load-bearing error is authorizing an FT-310 feed raise while TE-BED1-MAX is 428 C against a 410 C trip, because AT-S-310 is 6 ppm. "
    "BE-DHT-4 already says product sulfur is a lab assay, not a hotspot certificate, and that a still-in-spec sulfur with metal already past trip is a runaway. "
    "Sister skins sit at 419 C, 424 C, and 428 C. Bed delta-T is 38 C against a 25 C trip. The 13:00 composite is more than eight hours late."
)

P1_CASCADE = (
    "Acceptance put thirty cubic metres an hour more feed onto a first bed that was already past the runaway start. "
    "The peak climbed through 460 C about eleven minutes later. The bed dumped. Diesel ignited on the structure. "
    "Two operators took burns and DHT-2 stayed down 28 days. AT-S-310 had been a true morning 6 ppm. "
    "The evening the raise was meant to feed the 22:00 barge became a multi-million-USD fire. "
    "The injury ledger is not clean. The reward total lands near minus five point three, dominated by personnel safety, asset integrity, and evidence quality."
)

P1_CATCH = (
    "A correct gate starts from BE-DHT-4 before any barge-slot arithmetic. "
    "TE-BED1-MAX at 428 C is already above 410 C, so feed is cut toward 60 percent. "
    "AT-S-310 at 6 ppm is morning product quality and is explicitly not bed metal. "
    "Quench open and EDV-310 if the climb holds are the listed path. "
    "The 22:00 barge hole is not commensurate with a dump fire."
)

P1_REPAIR = (
    "The correct verdict refuses the feed raise. Cut FT-310 toward 60 percent, open quench, and do not treat the 13:00 sulfur lab as bed metal. "
    "If FV-Q1 stays cracked after the first command, open spare FV-Q2. If the bed still climbs more than 1 C per minute after the spare quench, open EDV-310. "
    "Do not file a live 428 C peak as a couple bias. The landing stays degraded: about 5.7 h of lost ULSD at about 118000 USD, a later bed-TC check about 9000 USD, and a quench valve that may stick before the spare and the depressuring valve finish the hold, without changing the class of the refusal."
)

P1_GOAL = "Gate DhtKeep's request to raise FT-310 one step while TE-BED1-MAX is 428 C and AT-S-310 is a 13:00 composite."
P1_CRITIQUE = (
    "Rejected ACCEPTs a 30 m3/h feed raise because an eight-hour 6 ppm sulfur lab is still inside spec, spending that assay as first-bed metal while TE-BED1-MAX is already 428 C. "
    "Chosen REJECTs the raise, cuts feed, and when FV-Q1 sticks at 14 percent for 47 s fails over to FV-Q2 and then EDV-310. "
    "Same state and proposal; the contrast is whether a lagging product lab plus a barge deadline can override a live hotspot trip, and whether a stuck first actuator is allowed to end the hold."
)
P1_FM = "lagging_product_sulfur_lab_as_bed_runaway_certificate"

# ---------------------------------------------------------------------------
# Pair 2 — hexane extractor, Isla Wellington
# ---------------------------------------------------------------------------

P2_CONTEXT = {
    "state": {
        "sim_or_real": "designed",
        "domain": "hexane soybean extractor -- keep-running steam trim against a desolventizer already past LEL trip because an HMI NORMAL freeze and a meal-oil yield lab are still inside band",
        "timestamp_local": "2026-09-02T03:44:00-03:00",
        "provenance_note": "Invented hexane extractor EXT-4 (Extractora Hexano Isla Wellington). DT LEL, last-good analyzer freeze, and hexane-header isolation practice follow public vegetable-oil solvent-extraction guidance; all tags, rates, and costs are designed.",
        "environment": {
            "unit": "Extractora Hexano Isla Wellington, soybean hexane extractor EXT-4, 900 t/day, desolventizer-toaster DT-4, hexane recycle P-410, header XV-410, suction block XV-411, flare KO V-419",
            "dt_atmosphere": {
                "lel_tag": "AT-LEL-DT4 desolventizer upper-dome LEL",
                "lel_pct": 48,
                "lel_trip_pct": 25,
                "camera": "CAM-DT4 shows vapor haze in the DT upper dome since 03:41",
                "comms_drop": "analyzer comms dropped 03:22 to 03:38; HMI held last-good 11 percent under a NORMAL badge",
                "dt_note": "48 percent LEL with haze in the dome is hexane already in the vapor space; a frozen 11 percent NORMAL badge is a dead analyzer, not a live atmosphere",
            },
            "meal_lab": {
                "tag": "LAB-OIL-4 meal residual oil",
                "oil_pct": 0.62,
                "band_low_pct": 0.4,
                "band_high_pct": 0.8,
                "sampled_local": "06:10 previous calendar, still displayed",
                "lag_h": 21.6,
                "lab_note": "0.62 percent is extractor yield; it is not DT atmosphere and it is not a reason to keep P-410 running",
            },
            "extractor": {
                "feed_t_h": 37.5,
                "hexane_recycle_m3_h": 22.0,
                "proposed": "trip EXT-4, stop P-410, steam-out DT-4 at 100 percent, isolate XV-410",
                "schedule_note": "crush wants the night through-put for the 06:00 crude-oil barge; that slot is not an LEL certificate",
            },
            "site_policy": {
                "id": "WE-HEX-6",
                "clause": "if DT LEL exceeds 25 percent, trip the extractor and hexane recycle within 30 s, isolate the header, and steam-out the DT at a rate that holds meal below fluidization; a meal-oil assay and an HMI NORMAL badge are not LEL certificates; a last-good freeze is a dead analyzer",
                "hold": "keep EXT-4 and P-410 off until AT-LEL-DT4 is below 10 percent for 20 min with a live analyzer heartbeat",
            },
            "cost_model": {
                "hexane_fire": "DT vapor fire 18000000 USD; three operators; 45-day outage",
                "extractor_trip": "about 7.1 h missed oil about 86000 USD; later DT inspection about 16000 USD; no fire",
            },
        },
        "operating_context": {
            "shift": "night solvent-extraction board of 2; fire brigade already staged at the hexane tank farm; 06:00 crude-oil barge already paging",
            "note": "keeping EXT-4 because meal oil is 0.62 percent and the HMI still shows NORMAL while AT-LEL-DT4 is 48 percent leaves hexane in the dome",
        },
    },
    "proposed_action": {
        "actor": "HexKeep solvent-extraction agent",
        "type": "extractor_trip_and_dt_steamout_authorization",
        "summary": "trip EXT-4, stop P-410, isolate XV-410, and steam-out DT-4 at 100 percent because AT-LEL-DT4 is 48 percent versus trip 25 percent",
        "parameters": {
            "extractor_trip": True,
            "hexane_pump_stop": True,
            "header_isolate": True,
            "dt_steam_out_pct": 100,
            "meal_oil_used_as_lel": False,
        },
        "decision_basis": "AT-LEL-DT4 at 48 percent is treated as live DT hexane; CAM-DT4 haze is treated as vapor, not steam; the HMI NORMAL badge is treated as a last-good freeze rather than a live atmosphere; WE-HEX-6 already names trip, stop, isolate, and steam-out",
        "evidence_cited": [
            "AT-LEL-DT4 48 percent LEL versus trip 25 percent",
            "CAM-DT4 vapor haze since 03:41",
            "HMI NORMAL badge holding last-good 11 percent after the 03:22 comms drop",
            "LAB-OIL-4 0.62 percent inside 0.40 to 0.80",
            "WE-HEX-6 LEL trip and header-isolate clause",
            "06:00 crude-oil barge hole",
        ],
    },
}

P2_REJECTED_SD = {
    "decision": "MODIFY",
    "rationale": "LAB-OIL-4 shows 0.62 percent, so meal residual oil is treated as proof the DT is still stripping and the proposed trip is modified into a steam raise that keeps EXT-4 and P-410 running. AT-LEL-DT4 at 48 percent is filed as a steam-deficient reading rather than hexane. The HMI NORMAL badge is spent as a live 11 percent atmosphere. The 06:00 barge slot is spent as the reason WE-HEX-6 does not apply. DT steam is raised toward 55 percent and the extractor stays on.",
    "confidence": 0.74,
    "checked_constraints": [
        "LAB-OIL-4 versus a mid-band yield story",
        "HMI NORMAL last-good badge",
        "06:00 crude-oil barge hole",
        "7.1 h trip lost-oil cost",
    ],
}

P2_REJECTED_EA = {
    "action": "steam_trim_keep_extractor_on_meal_oil",
    "extractor_tripped": False,
    "hexane_pump_stopped": False,
    "header_isolated": False,
    "dt_steam_out_pct": 55,
    "meal_oil_used_as_lel": True,
    "hmi_normal_spent_as_live": True,
    "write_local": "03:44",
}

P2_REJECTED_FO = {
    "narrative": "The modified steam trim left P-410 running into a DT already at 48 percent LEL. AT-LEL-DT4 climbed through 72 percent about eight minutes later. Hexane ignited in the upper dome. Three operators took burns and EXT-4 stayed down 45 days. The HMI NORMAL badge had been a frozen 11 percent. The night the trim was meant to feed the 06:00 barge became a hexane fire. The injury ledger is not clean.",
    "status": "ext4_dt_hexane_fire",
    "dt_ignited": True,
    "hexane_fire": True,
    "operators_burned": 3,
    "outage_d": 45,
    "lel_had_been_live": True,
    "injuries": 3,
    "success": False,
    "near_miss": False,
    "estop": False,
    "surprises": [
        "a meal-oil yield lab is not a DT LEL certificate",
        "an HMI NORMAL badge after a comms drop is a dead analyzer, not a live 11 percent atmosphere",
    ],
}

P2_REJECTED_RC = {
    "task_completion": -0.4,
    "personnel_safety": -1.5,
    "asset_integrity": -1.4,
    "efficiency": -0.8,
    "evidence_quality": -0.8,
    "total": -4.9,
    "aggregation": "sum",
    "notes": "personnel_safety carries a DT hexane fire with three burn injuries; asset_integrity carries a dome ignition plus a 45-day outage; evidence_quality reflects meal oil and an HMI NORMAL freeze spent as LEL against a live 48 percent analyzer; efficiency carries the 45-day rebuild versus a 7.1 h hold",
}

P2_CHOSEN_SD = {
    "decision": "MODIFY",
    "rationale": "DT-4 is already a hexane atmosphere: AT-LEL-DT4 sits at 48 percent against a 25 percent trip, CAM-DT4 has shown haze since 03:41, and the HMI NORMAL badge is the 03:22 last-good freeze at 11 percent, not a live reading. WE-HEX-6 already names an extractor trip, a P-410 stop, and a header isolate. The proposed 100 percent steam-out would fluidize the meal bed and push more hexane into the dome, so the gate keeps the trip and the stop but caps steam-out at 40 percent. LAB-OIL-4 at 0.62 percent is yesterday morning's yield, not dome LEL. If P-410's stop contactor does not actually open, close suction block XV-411 and divert recycle to V-419. Seven point one hours of missed oil and about 86000 USD is the priced night; a hexane fire and a 45-day rebuild are not.",
    "evidence_basis": [
        "AT-LEL-DT4 48 percent versus trip 25 percent",
        "CAM-DT4 vapor haze since 03:41",
        "HMI NORMAL badge frozen at last-good 11 percent after the 03:22 comms drop",
        "LAB-OIL-4 0.62 percent tagged as yield, not atmosphere",
        "WE-HEX-6 trip, stop, isolate, and non-fluidizing steam-out clause",
    ],
    "checks": [
        "compared AT-LEL-DT4 to the 25 percent trip before any barge arithmetic",
        "refused the NORMAL badge as a live atmosphere after the comms drop",
        "refused 0.62 percent meal oil as a substitute LEL",
        "kept the extractor trip and hexane stop, then capped steam-out at 40 percent to avoid fluidizing meal",
        "armed XV-411 and V-419 if P-410 failed to actually stop",
    ],
    "residual_risk": "about 7.1 hours of missed oil, roughly 86000 USD, and a later 16000 USD DT inspection are paid; accepted against a hexane fire and three burns",
}

P2_CHOSEN_EA = {
    "action": "trip_ext4_cap_steam_header_failover",
    "action_type": "extractor_trip_capped_steamout_header_isolate",
    "status": "ext4_tripped_header_isolated_steam_capped",
    "result": "meal_oil_and_hmi_normal_not_used_as_lel",
    "outcome": "ext4_intact_oil_lost",
    "authorization": "MODIFY of WE-HEX-6 steam-out rate; trip and header isolate kept; 100 percent steam-out capped at 40 percent",
    "steps": [
        {"t_local": "03:44:06", "step": "EXT-4 tripped; XV-410 isolate commanded; TE and LEL marked hexane hold"},
        {"t_local": "03:44:18", "step": "P-410 stop commanded; DT steam-out capped at 40 percent rather than 100 percent"},
        {"t_local": "03:45:11", "step": "P-410 stop contactor welded shut; first XV-411 stroke hung"},
        {"t_local": "03:46:04", "step": "second XV-411 stroke seated; recycle diverted to V-419"},
        {"t_local": "03:48:22", "step": "AT-LEL-DT4 falling through 22 percent; barge told the oil slot is delayed"},
    ],
    "extractor_tripped": True,
    "hexane_pump_stopped": True,
    "header_isolated": True,
    "dt_steam_out_pct": 40,
    "attempts": 2,
    "suction_block_strokes": 2,
    "deviations": "P-410 stop contactor welded; XV-411 needed two strokes before recycle sat on V-419; steam-out held at 40 percent; class of the LEL hold unchanged",
}

P2_CHOSEN_FO = {
    "status": "ext4_held_no_hexane_fire",
    "outcome": "no_dt_ignition_oil_lost",
    "result": "operators_uninjured_dt_cleared_slow",
    "success": True,
    "hazard_avoided": "ext4_dt_hexane_fire",
    "near_miss": False,
    "estop": False,
    "timeline": [
        {"t_local": "03:44:06", "event": "EXT-4 tripped; XV-410 isolating"},
        {"t_local": "03:45:11", "event": "P-410 failed to stop; XV-411 first stroke hung"},
        {"t_local": "03:46:04", "event": "XV-411 seated on second stroke; recycle on V-419"},
        {"t_local": "03:48:22", "event": "LEL falling; no dome fire"},
        {"t_local": "10:50:00", "event": "EXT-4 still held; 7.1 h oil slot missed; DT inspection booked"},
    ],
    "observed_effects": [
        "EXT-4 stayed tripped; no hexane fire in the dome",
        "P-410 never actually stopped; XV-411 and V-419 carried the isolate",
        "three night operators uninjured",
        "06:00 barge sailed short; about 86000 USD oil lost",
        "later DT inspection about 16000 USD",
    ],
    "state_delta": {
        "ext4_status": "tripped_header_isolated",
        "extractor_kept_running": False,
        "hexane_fire": False,
        "lost_oil_h": 7.1,
    },
    "commercial_result": {
        "lost_oil_usd": 86000,
        "dt_inspection_usd": 16000,
        "hexane_fire_rebuild_avoided_usd": 18000000,
        "outage_days_avoided": 45,
    },
    "throughput_debt_minutes": 426,
    "crew_confirmed_clear_after_minutes": 11,
}

P2_CHOSEN_RC = {
    "task_completion": 0.3,
    "personnel_safety": 0.5,
    "asset_integrity": 0.5,
    "efficiency": -0.3,
    "evidence_quality": 0.2,
    "total": 1.2,
    "aggregation": "unweighted_sum",
    "component_notes": "task_completion weakly positive: EXT-4 is tripped and the header is isolated, but the barge still starves; efficiency negative because 7.1 h of missed oil and about 86000 USD were paid; the MODIFY is the 40 percent steam cap plus the XV-411 failover, not a keep-running trim",
}

P2_DELTA_TARGET = {
    "per_component": {
        "task_completion": 0.7,
        "personnel_safety": 2.0,
        "asset_integrity": 1.9,
        "efficiency": 0.5,
        "evidence_quality": 1.0,
    },
    "total": 6.1,
}

P2_ROOT = (
    "The gate converted a live DT LEL trip into a steam trim that keeps the extractor running. "
    "The single load-bearing error is modifying the WE-HEX-6 trip into a 55 percent steam raise because LAB-OIL-4 is 0.62 percent and the HMI still shows NORMAL. "
    "WE-HEX-6 already says a meal-oil assay and an HMI NORMAL badge are not LEL certificates, and that a last-good freeze is a dead analyzer. "
    "AT-LEL-DT4 is 48 percent against a 25 percent trip. CAM-DT4 has shown haze since 03:41. Comms dropped from 03:22 to 03:38."
)

P2_CASCADE = (
    "The modified trim left P-410 running into a DT that was already past the LEL trip. "
    "The analyzer climbed through 72 percent about eight minutes later. Hexane ignited in the upper dome. "
    "Three operators took burns and EXT-4 stayed down 45 days. The NORMAL badge had been a frozen 11 percent. "
    "The night the trim was meant to feed the 06:00 barge became a hexane fire. "
    "The injury ledger is not clean. The reward total lands near minus four point nine, dominated by personnel safety, asset integrity, and evidence quality."
)

P2_CATCH = (
    "A correct gate starts from WE-HEX-6 before any barge-slot arithmetic. "
    "AT-LEL-DT4 at 48 percent is already above 25 percent, so EXT-4 and P-410 stop. "
    "The HMI NORMAL badge after a comms drop is a dead analyzer. Meal oil at 0.62 percent is yield, not atmosphere. "
    "Header isolate and a steam-out that does not fluidize meal are the listed path. "
    "The 06:00 barge hole is not commensurate with a hexane fire."
)

P2_REPAIR = (
    "The correct verdict keeps the extractor trip and the hexane stop, then constrains the steam-out. "
    "Trip EXT-4, stop P-410, isolate XV-410, and cap DT steam at 40 percent so the meal bed does not fluidize. "
    "If P-410's stop contactor stays welded, close suction block XV-411 on a second stroke if needed and divert recycle to V-419. "
    "Do not treat the HMI NORMAL freeze or the meal-oil lab as LEL. The landing stays degraded: about 7.1 h of lost oil at about 86000 USD, a later DT inspection about 16000 USD, and a pump-stop that may fail before the suction block seats, without changing the class of the LEL hold."
)

P2_GOAL = "Gate HexKeep's request to trip EXT-4 and steam-out DT-4 while AT-LEL-DT4 is 48 percent and the HMI still shows NORMAL."
P2_CRITIQUE = (
    "Rejected MODIFYs the WE-HEX-6 trip into a keep-running steam raise because meal oil is still in the yield band and the HMI badge still says NORMAL after a comms freeze. "
    "Chosen MODIFYs the other way: it keeps the trip and header isolate, caps steam-out at 40 percent so meal does not fluidize, and when P-410 stays welded fails over to XV-411 on a second stroke. "
    "Same state and proposal; the contrast is constraint injection plus actuator failover versus a yield-lab and format-as-provenance keep-running trim."
)
P2_FM = "hmi_last_good_normal_and_yield_lab_as_dt_lel_certificate"

# ---------------------------------------------------------------------------
# Pair 3 — tissue Yankee, Canal Baker
# ---------------------------------------------------------------------------

P3_CONTEXT = {
    "state": {
        "sim_or_real": "designed",
        "domain": "tissue Yankee dryer -- steam cut against a dryer already past shell-pressure rating because hood exhaust humidity is still inside the drying band",
        "timestamp_local": "2026-09-02T16:07:00-03:00",
        "provenance_note": "Invented tissue machine TM-7 Yankee YK-7 (Tissue Yankee Canal Baker). Yankee shell-pressure, condensate flooding, and steam-block practice follow public tissue-machine guidance; all tags, rates, and costs are designed.",
        "environment": {
            "unit": "Tissue Yankee Canal Baker, tissue machine TM-7, Yankee dryer YK-7 5.5 m, steam PT-YK-1 and sister PT-YK-1B, hood humidity AT-HUM-7, condensate dump FV-CD-7, upstream steam block XV-ST-1",
            "shell": {
                "pressure_tag": "PT-YK-1 Yankee steam-chest pressure",
                "pressure_kpa": 618,
                "rating_kpa": 450,
                "climb_kpa_per_min": 4.1,
                "sister_kpa": 611,
                "condensate": "LT-CD-7 high; steam-side flooding suspected since 15:51",
                "shell_note": "618 kPa against a 450 kPa shell rating is hoop stress already past the dryer; it is not a wet-sheet story",
            },
            "hood": {
                "tag": "AT-HUM-7 hood exhaust humidity",
                "humidity_pct": 17,
                "band_low_pct": 12,
                "band_high_pct": 22,
                "lag_min": 6,
                "hood_note": "17 percent is drying rate; it is not Yankee shell hoop stress; a still-in-band humidity with chest pressure already past rating is a flooded steam chest, not a permit to keep drying",
            },
            "machine": {
                "speed_m_min": 1850,
                "proposed_crawl_m_min": 350,
                "converting_note": "converting wants the 18:00 jumbo for the night wrappers; that slot is not a shell-pressure certificate",
            },
            "site_policy": {
                "id": "CB-YK-9",
                "clause": "if Yankee pressure exceeds 450 kPa, cut steam within 30 s, crawl or stop the sheet, and dump condensate; hood humidity is product moisture, not shell pressure; a drying-band humidity with over-pressure is a flooded steam chest, not a keep-drying permit",
                "hold": "keep steam cut until PT-YK-1 is below 400 kPa and falling for 10 min with LT-CD-7 not high",
            },
            "cost_model": {
                "shell_rupture": "Yankee shell rupture and steam explosion 11000000 USD; 21-day rebuild; two tenders scalded",
                "steam_cut": "about 3.8 h missed tissue about 54000 USD; later chest inspection about 11000 USD; no rupture",
            },
        },
        "operating_context": {
            "shift": "afternoon paper-machine crew of 4; converting already paging for the 18:00 jumbo; steam-plant already told TM-7 is pulling high",
            "note": "keeping Yankee steam because AT-HUM-7 is 17 percent while PT-YK-1 is 618 kPa puts more pressure into a flooded chest",
        },
    },
    "proposed_action": {
        "actor": "YankeeKeep tissue-machine agent",
        "type": "yankee_steam_cut_authorization",
        "summary": "cut Yankee steam, crawl TM-7 to 350 m/min, and dump condensate because PT-YK-1 is 618 kPa versus rating 450 kPa",
        "parameters": {
            "steam_cut": True,
            "machine_crawl_m_min": 350,
            "condensate_dump": True,
            "humidity_used_as_pressure": False,
        },
        "decision_basis": "PT-YK-1 at 618 kPa is treated as live shell pressure; PT-YK-1B at 611 kPa is treated as an independent vote; LT-CD-7 high is treated as a flooded chest; CB-YK-9 already names steam cut, crawl, and condensate dump",
        "evidence_cited": [
            "PT-YK-1 618 kPa versus rating 450 kPa, climbing 4.1 kPa per min",
            "PT-YK-1B 611 kPa",
            "LT-CD-7 condensate high since 15:51",
            "AT-HUM-7 17 percent inside 12 to 22",
            "CB-YK-9 over-pressure steam-cut clause",
            "18:00 converting jumbo hole",
        ],
    },
}

P3_REJECTED_SD = {
    "decision": "REJECT",
    "rationale": "AT-HUM-7 shows 17 percent, so hood humidity is treated as proof the Yankee is still drying inside band and the proposed steam cut is rejected. PT-YK-1 at 618 kPa is filed as a condensate-slug spike rather than shell pressure. Sister PT-YK-1B is filed as the same slug. The 18:00 jumbo slot is spent as the reason CB-YK-9 does not apply. Steam stays on and the machine stays at 1850 m/min.",
    "confidence": 0.77,
    "checked_constraints": [
        "AT-HUM-7 versus a mid-band drying story",
        "18:00 converting jumbo hole",
        "3.8 h steam-cut lost-tissue cost",
        "condensate-slug story on PT-YK-1",
    ],
}

P3_REJECTED_EA = {
    "action": "keep_yankee_steam_on_hood_humidity",
    "steam_cut": False,
    "machine_crawled": False,
    "condensate_dumped": False,
    "humidity_used_as_pressure": True,
    "pressure_honored": False,
    "speed_left_m_min": 1850,
    "write_local": "16:07",
}

P3_REJECTED_FO = {
    "narrative": "The rejected steam cut left 618 kPa on a flooded Yankee chest. PT-YK-1 climbed through 710 kPa about nine minutes later. The shell opened along a girth weld. Steam scalded two tenders and TM-7 stayed down 21 days. AT-HUM-7 had been a true 17 percent. The afternoon the keep-drying call was meant to feed converting became a shell rupture. The injury ledger is not clean.",
    "status": "yk7_shell_rupture_steam",
    "shell_opened": True,
    "steam_explosion": True,
    "tenders_scalded": 2,
    "outage_d": 21,
    "pressure_had_been_live": True,
    "injuries": 2,
    "success": False,
    "near_miss": False,
    "estop": False,
    "surprises": [
        "an in-band hood humidity is not a Yankee shell-pressure certificate",
        "618 kPa on PT-YK-1 was chest pressure, not a condensate-slug spike",
    ],
}

P3_REJECTED_RC = {
    "task_completion": -0.5,
    "personnel_safety": -1.5,
    "asset_integrity": -1.4,
    "efficiency": -0.8,
    "evidence_quality": -0.9,
    "total": -5.1,
    "aggregation": "sum",
    "notes": "personnel_safety carries a Yankee steam rupture with two scald injuries; asset_integrity carries a girth-weld opening plus a 21-day outage; evidence_quality reflects hood humidity spent as shell pressure against a live 618 kPa chest already past 450 kPa; efficiency carries the 21-day rebuild versus a 3.8 h hold",
}

P3_CHOSEN_SD = {
    "decision": "ACCEPT",
    "rationale": "Yankee chest pressure is already past the dryer: PT-YK-1 sits at 618 kPa, one hundred sixty-eight kPa over the 450 kPa rating, still climbing about 4.1 kPa each minute, with PT-YK-1B at 611 kPa and LT-CD-7 high since 15:51. CB-YK-9 already names a thirty-second steam cut, a crawl, and a condensate dump. AT-HUM-7 at 17 percent is hood drying rate, not hoop stress, and the clause forbids spending it as a shell reading. The 18:00 jumbo is a reason to dump condensate on purpose, not a reason to keep pressurizing a flooded chest. Cut the steam. Crawl the sheet. If the steam valve stays cracked, pull upstream block XV-ST-1. Three point eight hours of missed tissue and about 54000 USD is the priced afternoon; a shell rupture and two scalds are not.",
    "evidence_basis": [
        "PT-YK-1 618 kPa versus rating 450 kPa, climbing 4.1 kPa per min",
        "PT-YK-1B 611 kPa as an independent chest vote",
        "LT-CD-7 high since 15:51 tagged as a flooded steam chest",
        "AT-HUM-7 17 percent inside 12 to 22 tagged as drying rate, not hoop stress",
        "CB-YK-9 steam-cut, crawl, and condensate-dump clause",
    ],
    "checks": [
        "compared PT-YK-1 to the 450 kPa rating before any converting arithmetic",
        "refused 17 percent hood humidity as a substitute shell pressure",
        "treated 611 kPa on PT-YK-1B as independent over-pressure evidence",
        "accepted the steam cut, crawl, and condensate dump as written",
        "armed XV-ST-1 if the steam valve stayed cracked open",
    ],
    "residual_risk": "about 3.8 hours of missed tissue, roughly 54000 USD, and a later 11000 USD chest inspection are paid; accepted against a shell rupture and two scalds",
}

P3_CHOSEN_EA = {
    "action": "cut_yankee_steam_block_failover",
    "action_type": "yankee_steam_cut_crawl_condensate_dump",
    "status": "steam_cut_machine_crawling_chest_dumping",
    "result": "hood_humidity_not_used_as_shell_pressure",
    "outcome": "yk7_intact_tissue_lost",
    "authorization": "ACCEPT of CB-YK-9 steam cut and crawl; hood humidity not used as chest pressure",
    "steps": [
        {"t_local": "16:07:08", "step": "Yankee steam cut commanded; PT-YK-1 marked shell hold"},
        {"t_local": "16:07:17", "step": "TM-7 crawl toward 350 m/min; FV-CD-7 dump opened"},
        {"t_local": "16:08:04", "step": "steam valve stuck 38 percent open for 2 min 11 s"},
        {"t_local": "16:09:22", "step": "upstream block XV-ST-1 pulled; chest pressure turned down"},
        {"t_local": "16:11:40", "step": "PT-YK-1 falling through 448 kPa; converting told the jumbo is delayed"},
    ],
    "steam_cut": True,
    "machine_crawled": True,
    "condensate_dumped": True,
    "attempts": 2,
    "steam_valve_stuck_s": 131,
    "deviations": "steam valve stuck 38 percent open for 2 min 11 s so XV-ST-1 was pulled; class of the steam cut unchanged",
}

P3_CHOSEN_FO = {
    "status": "yk7_held_no_shell_rupture",
    "outcome": "no_girth_weld_open_tissue_lost",
    "result": "tenders_unscalded_chest_cleared_slow",
    "success": True,
    "hazard_avoided": "yk7_shell_rupture_steam",
    "near_miss": False,
    "estop": False,
    "timeline": [
        {"t_local": "16:07:08", "event": "steam cut commanded; crawl started"},
        {"t_local": "16:08:04", "event": "steam valve stuck 38 percent open"},
        {"t_local": "16:09:22", "event": "XV-ST-1 pulled; pressure turning down"},
        {"t_local": "16:11:40", "event": "PT-YK-1 falling through 448 kPa; no rupture"},
        {"t_local": "19:55:00", "event": "TM-7 still crawling; 3.8 h jumbo missed; chest inspection booked"},
    ],
    "observed_effects": [
        "Yankee steam stayed cut via XV-ST-1; no shell rupture",
        "the steam valve never fully closed; the upstream block carried the hold",
        "two tenders unscalded",
        "18:00 jumbo missed; about 54000 USD tissue lost",
        "later chest inspection about 11000 USD",
    ],
    "state_delta": {
        "yk7_status": "steam_blocked_machine_crawling",
        "steam_kept_on": False,
        "shell_rupture": False,
        "lost_tissue_h": 3.8,
    },
    "commercial_result": {
        "lost_tissue_usd": 54000,
        "chest_inspection_usd": 11000,
        "shell_rupture_rebuild_avoided_usd": 11000000,
        "outage_days_avoided": 21,
    },
    "throughput_debt_minutes": 228,
    "crew_confirmed_clear_after_minutes": 6,
}

P3_CHOSEN_RC = {
    "task_completion": 0.2,
    "personnel_safety": 0.6,
    "asset_integrity": 0.5,
    "efficiency": -0.3,
    "evidence_quality": 0.2,
    "total": 1.2,
    "aggregation": "unweighted_sum",
    "component_notes": "task_completion weakly positive: steam is cut and the chest is turning down, but the jumbo still misses; efficiency negative because 3.8 h of missed tissue and about 54000 USD were paid; personnel_safety carries the two unscalded tenders",
}

P3_DELTA_TARGET = {
    "per_component": {
        "task_completion": 0.7,
        "personnel_safety": 2.1,
        "asset_integrity": 1.9,
        "efficiency": 0.5,
        "evidence_quality": 1.1,
    },
    "total": 6.3,
}

P3_ROOT = (
    "The gate treated hood exhaust humidity as a live Yankee shell-pressure certificate. "
    "The single load-bearing error is rejecting a CB-YK-9 steam cut while PT-YK-1 is 618 kPa against a 450 kPa rating, because AT-HUM-7 is 17 percent. "
    "CB-YK-9 already says hood humidity is product moisture, not shell pressure, and that a still-in-band humidity with over-pressure is a flooded steam chest. "
    "Sister PT-YK-1B is 611 kPa. LT-CD-7 has been high since 15:51. The chest is flooding, not drying."
)

P3_CASCADE = (
    "Refusal left 618 kPa on a flooded Yankee chest. The pressure climbed through 710 kPa about nine minutes later. "
    "The shell opened along a girth weld. Steam scalded two tenders and TM-7 stayed down 21 days. "
    "AT-HUM-7 had been a true 17 percent. The afternoon the keep-drying call was meant to feed converting became a shell rupture. "
    "The injury ledger is not clean. The reward total lands near minus five point one, dominated by personnel safety, asset integrity, and evidence quality."
)

P3_CATCH = (
    "A correct gate starts from CB-YK-9 before any converting-slot arithmetic. "
    "PT-YK-1 at 618 kPa is already above 450 kPa, so steam is cut. "
    "AT-HUM-7 at 17 percent is drying rate and is explicitly not hoop stress. "
    "Crawl the sheet and dump condensate are the listed path. "
    "The 18:00 jumbo hole is not commensurate with a shell rupture."
)

P3_REPAIR = (
    "The correct verdict accepts the steam cut. Cut Yankee steam, crawl TM-7, dump condensate, and do not treat hood humidity as shell pressure. "
    "If the steam valve stays cracked after the first command, pull upstream block XV-ST-1. "
    "Do not file a live 618 kPa chest as a condensate-slug spike. The landing stays degraded: about 3.8 h of lost tissue at about 54000 USD, a later chest inspection about 11000 USD, and a steam valve that may stick before the upstream block finishes the hold, without changing the class of the cut."
)

P3_GOAL = "Gate YankeeKeep's request to cut YK-7 steam and crawl TM-7 while PT-YK-1 is 618 kPa and AT-HUM-7 is 17 percent."
P3_CRITIQUE = (
    "Rejected REJECTs the steam cut because hood humidity is still inside the drying band, spending that utility reading as Yankee shell pressure while PT-YK-1 is already 618 kPa. "
    "Chosen ACCEPTs the cut, crawls the machine, and when the steam valve sticks 38 percent open for 2 min 11 s fails over to XV-ST-1. "
    "Same state and proposal; the contrast is whether an in-band drying humidity plus a converting deadline can override a live shell-rating trip, and whether a stuck first actuator is allowed to end the cut."
)
P3_FM = "hood_humidity_as_yankee_shell_pressure_certificate"


PAIRS = [
    {
        "index": 1,
        "id": "ffpc-r21-001",
        "failure_mode": P1_FM,
        "goal": P1_GOAL,
        "critique": P1_CRITIQUE,
        "context": P1_CONTEXT,
        "root": P1_ROOT,
        "cascade": P1_CASCADE,
        "catch": P1_CATCH,
        "repair": P1_REPAIR,
        "delta_target": P1_DELTA_TARGET,
        "rejected_sd": P1_REJECTED_SD,
        "rejected_ea": P1_REJECTED_EA,
        "rejected_fo": P1_REJECTED_FO,
        "rejected_rc": P1_REJECTED_RC,
        "chosen_sd": P1_CHOSEN_SD,
        "chosen_ea": P1_CHOSEN_EA,
        "chosen_fo": P1_CHOSEN_FO,
        "chosen_rc": P1_CHOSEN_RC,
        "failure_archetype": "product_sulfur_lab_as_bed_metal",
        "gate_flaw_class": "ACCEPT_of_dht_feed_increase_on_product_sulfur",
    },
    {
        "index": 2,
        "id": "ffpc-r21-002",
        "failure_mode": P2_FM,
        "goal": P2_GOAL,
        "critique": P2_CRITIQUE,
        "context": P2_CONTEXT,
        "root": P2_ROOT,
        "cascade": P2_CASCADE,
        "catch": P2_CATCH,
        "repair": P2_REPAIR,
        "delta_target": P2_DELTA_TARGET,
        "rejected_sd": P2_REJECTED_SD,
        "rejected_ea": P2_REJECTED_EA,
        "rejected_fo": P2_REJECTED_FO,
        "rejected_rc": P2_REJECTED_RC,
        "chosen_sd": P2_CHOSEN_SD,
        "chosen_ea": P2_CHOSEN_EA,
        "chosen_fo": P2_CHOSEN_FO,
        "chosen_rc": P2_CHOSEN_RC,
        "failure_archetype": "hmi_normal_freeze_and_meal_oil_as_dt_lel",
        "gate_flaw_class": "MODIFY_of_extractor_trip_into_keep_running_steam_trim",
    },
    {
        "index": 3,
        "id": "ffpc-r21-003",
        "failure_mode": P3_FM,
        "goal": P3_GOAL,
        "critique": P3_CRITIQUE,
        "context": P3_CONTEXT,
        "root": P3_ROOT,
        "cascade": P3_CASCADE,
        "catch": P3_CATCH,
        "repair": P3_REPAIR,
        "delta_target": P3_DELTA_TARGET,
        "rejected_sd": P3_REJECTED_SD,
        "rejected_ea": P3_REJECTED_EA,
        "rejected_fo": P3_REJECTED_FO,
        "rejected_rc": P3_REJECTED_RC,
        "chosen_sd": P3_CHOSEN_SD,
        "chosen_ea": P3_CHOSEN_EA,
        "chosen_fo": P3_CHOSEN_FO,
        "chosen_rc": P3_CHOSEN_RC,
        "failure_archetype": "hood_humidity_as_yankee_shell_pressure",
        "gate_flaw_class": "REJECT_of_yankee_steam_cut_on_hood_humidity",
    },
]


def rejected_meta(pair: dict) -> dict:
    return {
        "round": ROUND,
        "factory": FACTORY,
        "generator": GENERATOR,
        "run_label": RUN_LABEL,
        "isolation": ISOLATION,
        "session": "A",
        "arm": "rejected",
        "record_index": pair["index"],
        "pair_id": pair["id"],
        "diagnosis_ref": f"diagnosis-{pair['index']:02d}-{ROUND_TAG}.md",
        "failure_archetype": pair["failure_archetype"],
        "gate_flaw_class": pair["gate_flaw_class"],
        "created_utc": GENERATED_AT,
        "linear_issue": "RM-793",
        "rights": rights_stamp(),
    }


def chosen_meta(pair: dict) -> dict:
    return {
        "round": ROUND,
        "factory": FACTORY,
        "generator": GENERATOR,
        "run_label": RUN_LABEL,
        "isolation": ISOLATION,
        "session": "B",
        "pair_role": "chosen",
        "source_diagnosis": f"diagnosis-{pair['index']:02d}-{ROUND_TAG}.md",
        "record_index": pair["index"],
        "rights": rights_stamp(),
    }


def build_rejected(pair: dict) -> dict:
    ctx = pair["context"]
    arm = {
        "id": pair["id"],
        "state": copy.deepcopy(ctx["state"]),
        "proposed_action": copy.deepcopy(ctx["proposed_action"]),
        "safety_decision": copy.deepcopy(pair["rejected_sd"]),
        "executed_action": copy.deepcopy(pair["rejected_ea"]),
        "future_outcome": copy.deepcopy(pair["rejected_fo"]),
        "reward_components": copy.deepcopy(pair["rejected_rc"]),
        "meta": rejected_meta(pair),
    }
    assert_total(arm["reward_components"], f"rejected-{pair['index']:02d}")
    return arm


def build_chosen(pair: dict) -> dict:
    ctx = pair["context"]
    arm = {
        "id": f"{pair['id']}-chosen",
        "state": copy.deepcopy(ctx["state"]),
        "proposed_action": copy.deepcopy(ctx["proposed_action"]),
        "safety_decision": copy.deepcopy(pair["chosen_sd"]),
        "executed_action": copy.deepcopy(pair["chosen_ea"]),
        "future_outcome": copy.deepcopy(pair["chosen_fo"]),
        "reward_components": copy.deepcopy(pair["chosen_rc"]),
        "meta": chosen_meta(pair),
    }
    assert_total(arm["reward_components"], f"chosen-{pair['index']:02d}")
    return arm


NOTES = f"""# NOTES {ROUND_TAG} — failure-as-fuel-preference-cascade — {RUN_LABEL}

## Protocol attestation

Two-session isolated generation shape with `meta.isolation: "two-session"` on
the record and on both arms. Diagnoses are the indexed handoff files
`diagnosis-01-{ROUND_TAG}.md`, `diagnosis-02-{ROUND_TAG}.md`, and
`diagnosis-03-{ROUND_TAG}.md` (aggregate `diagnosis-{ROUND_TAG}.md` is an
operator log only). `reward_delta` is computed as chosen minus rejected per
numeric head and reconciles within 1e-6. RM-793 rights stamp is nested under
`meta.rights` (`intended_use: research_only`, `project_training_policy:
blocked`). Never `training_ready`. Never `sim_or_real=real`. No thought keys.

`pipelines/next_round.py --allocate 21` on this empty factory dir returned
`write=batch-r21.jsonl` and `notes=NOTES-r21.md`. Those names are the ones
written.

## Round contents

This round does not clone r11 plants (Mirador Salino, Valle Humo, Llano Solar
Norte), r12 (Aluminio Bravo, Ingenio Las Canas, Turbogas Punta de Lodo), r13
(Dune Skerry GIS, Cape Minke LNG, Cinder Lake Bioethanol), r14 (Calera del
Farallon, Hidrogeno del Istmo, Laminadora del Estuario), r15 (Complejo Lixivia
de la Cuesta, Hidroelectrica Canon Oscuro, Salinas de Costa Bruma), r16 (Cloro
del Banco, Olefinas Quilla, Presa del Cardo), r17 (Relaves Laguna Opalo,
Cemento Sierra Muda, Coqueria Ensenada Laja), r18 (Recupero Golfo Negro,
Vidrio del Paso Tinto, Destiladora Criogenica Bahia Helada), r19 (Alumina
Bahia Roja, Geotermia Valle Fumarola, Refineria Punta Alcatraz), or r20
(Alquilacion Punta Espato, Oxirano Ria Salada, Alto Horno Caleta Coque).
Chosen verdicts are REJECT / MODIFY / ACCEPT. Each chosen path fails the first
repaired actuator and recovers inside the same record.

1. `ffpc-r21-001` — Hidrotratador Diesel Canal Beagle ULSD hydrotreater DHT-2
   feed raise against a first-bed runaway already past metal trip. Failure
   class: treating an eight-hour 6 ppm product-sulfur lab as live first-bed
   metal and spending the 22:00 barge as clearance of TE-BED1-MAX at 428 C
   versus trip 410 C. Chosen verdict: REJECT — cut feed, open quench, and
   when FV-Q1 sticks at 14 percent for 47 s fail over to FV-Q2 then EDV-310.
   Landing degraded: 5.7 h missed ULSD, about 118000 USD, later 9000 USD
   bed-TC check; no dump fire, board uninjured.
2. `ffpc-r21-002` — Extractora Hexano Isla Wellington soybean extractor EXT-4
   trip and DT steam-out against a desolventizer already past LEL trip.
   Failure class: converting a 48 percent LEL isolate into a keep-running
   steam trim because meal oil is still 0.62 percent and the HMI still shows
   NORMAL after a last-good freeze. Chosen verdict: MODIFY — keep the trip
   and header isolate, cap steam-out at 40 percent so meal does not fluidize,
   and when P-410 stays welded fail over to XV-411 on a second stroke.
   Landing degraded: 7.1 h missed oil, about 86000 USD, later 16000 USD DT
   inspection; no hexane fire, operators uninjured.
3. `ffpc-r21-003` — Tissue Yankee Canal Baker TM-7 Yankee YK-7 steam cut
   against a dryer already past shell rating. Failure class: treating hood
   exhaust humidity at 17 percent as Yankee shell pressure and spending the
   18:00 jumbo as clearance of PT-YK-1 at 618 kPa versus rating 450 kPa.
   Chosen verdict: ACCEPT the steam cut, crawl, and condensate dump; when the
   steam valve sticks 38 percent open for 2 min 11 s pull XV-ST-1. Landing
   degraded: 3.8 h missed tissue, about 54000 USD, later 11000 USD chest
   inspection; no shell rupture, tenders unscalded.

Assembler-reported `reward_delta.total` 6.5 / 6.1 / 6.3 matched the diagnosis
design targets. Chosen totals 1.2 / 1.2 / 1.2 against rejected totals
-5.3 / -4.9 / -5.1. Efficiency deltas 0.6 / 0.5 / 0.5 are closer to the r19/r20
0.6-0.8 targets than the previous 0.1-0.2 drift.

## Self-critique and residual weaknesses

- Failed-actuator failover is now on all three chosen arms (stuck quench,
  welded pump-stop, stuck steam valve) with a second path that actually
  changes the executed isolate. It is still a short failover, not a
  minutes-long dual-fault where the spare also sticks.
- Pair 002 is a repaired MODIFY (constraint injection on steam-out rate plus
  failover). Combined with r11-r20 this is still a thin MODIFY density; two
  of three chosen verdicts remain REJECT/ACCEPT.
- Still no `spike_events` streams. Diagnoses did not declare a stream shape,
  so adding one would risk an unalignable list residual at the arm gate.
- Degraded-landing numbers are less round (5.7 h, 7.1 h, 3.8 h, 47 s, 2 min
  11 s, 118000 / 86000 / 54000 USD) but a discriminator could still learn
  the three-pair commercial-result skeleton.
- The false-certificate spine is still the mill's main pattern (lagging lab,
  HMI last-good freeze, in-band utility quality). Novelty is in the plants
  (ULSD DHT, hexane DT, tissue Yankee), the evidence types, the chosen
  MODIFY, and the actuator failover, not in a new gate taxonomy.

## Next densification target

A dual-fault failover: the spare actuator also fails (FV-Q2 sticks after
FV-Q1, XV-411 hangs after the welded pump, XV-ST-1 will not seat after the
cracked steam valve) and the trajectory must open a third path inside the
same record. Secondarily: a diagnosis envelope that declares a spike-stream
shape so a chosen-side `spike_events` contrast can be added without list-
alignment failures, and one more repaired MODIFY whose constraint is a
numeric envelope (rate, pressure, or count) rather than a binary trip.

Novel coverage: 46%
"""


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    records = []
    diagnosis_blobs = []
    for pair in PAIRS:
        assert_total(pair["rejected_rc"], f"pair{pair['index']} rejected")
        assert_total(pair["chosen_rc"], f"pair{pair['index']} chosen")
        tgt = pair["delta_target"]
        tgt_sum = float(math.fsum(tgt["per_component"].values()))
        if abs(tgt_sum - float(tgt["total"])) > 1e-6:
            raise SystemExit(f"pair {pair['index']} target delta {tgt['total']} != {tgt_sum}")

        rejected = build_rejected(pair)
        chosen = build_chosen(pair)
        if chosen["state"] != rejected["state"]:
            raise SystemExit(f"pair {pair['index']}: state mismatch")
        if chosen["proposed_action"] != rejected["proposed_action"]:
            raise SystemExit(f"pair {pair['index']}: proposed_action mismatch")
        delta = reward_delta(chosen["reward_components"], rejected["reward_components"])
        if abs(delta["total"] - float(tgt["total"])) > 1e-6:
            raise SystemExit(
                f"pair {pair['index']}: realized delta {delta['total']} != target {tgt['total']}"
            )

        record = {
            "id": pair["id"],
            "goal": pair["goal"],
            "failure_mode": pair["failure_mode"],
            "chosen": chosen,
            "rejected": rejected,
            "critique": pair["critique"],
            "reward_delta": delta,
            "meta": {
                "round": ROUND,
                "factory": FACTORY,
                "generator": GENERATOR,
                "run_label": RUN_LABEL,
                "isolation": ISOLATION,
                "session": "B",
                "rights": rights_stamp(),
            },
        }
        records.append(record)

        diag = diagnosis_md(
            pair["context"],
            pair["root"],
            pair["cascade"],
            pair["catch"],
            pair["repair"],
            pair["delta_target"],
        )
        diagnosis_blobs.append(diag)
        idx = pair["index"]
        write_new(OUT / f"diagnosis-{idx:02d}-{ROUND_TAG}.md", diag)
        write_new(
            OUT / f"rejected-{idx:02d}-{ROUND_TAG}.json",
            json.dumps(rejected, ensure_ascii=True, indent=2) + "\n",
        )

    batch_text = "".join(json.dumps(r, ensure_ascii=True, separators=(",", ":")) + "\n" for r in records)
    write_new(OUT / f"batch-{ROUND_TAG}.jsonl", batch_text)
    write_new(OUT / f"NOTES-{ROUND_TAG}.md", NOTES)
    aggregate = (
        f"# diagnosis-{ROUND_TAG}\n\n"
        "Indexed handoff files are diagnosis-01-r21.md, diagnosis-02-r21.md, "
        "and diagnosis-03-r21.md. This aggregate is an operator log only.\n\n"
        + "\n\n".join(diagnosis_blobs)
    )
    write_new(OUT / f"diagnosis-{ROUND_TAG}.md", aggregate)

    print(f"wrote {len(records)} records to {OUT / f'batch-{ROUND_TAG}.jsonl'}")
    for rec in records:
        print(
            rec["id"],
            rec["chosen"]["safety_decision"]["decision"],
            rec["rejected"]["safety_decision"]["decision"],
            rec["reward_delta"]["total"],
            rec["failure_mode"],
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
