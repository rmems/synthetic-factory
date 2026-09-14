#!/usr/bin/env python3
"""CREATE-ONLY FFPC Session A round 65 into the live 2026-09-02 tree."""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
DEST = (
    REPO
    / "outputs"
    / "raw"
    / "2026-09-02-final-heavy"
    / "failure-as-fuel-preference-cascade"
)
sys.path.insert(0, str(REPO / "pipelines"))
from preference_arms_diagnosis import validate_diagnosis_document  # noqa: E402
from preference_arms_text import PreferenceArmsError  # noqa: E402

ROUND = 65
CREATED = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
FORBIDDEN_KEYS = {"real", "thought"}
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
    "linear_issue": "RM-793",
}
REQUIRED_TOP = (
    "id",
    "state",
    "proposed_action",
    "safety_decision",
    "executed_action",
    "future_outcome",
    "reward_components",
    "provenance",
    "meta",
)
REWARD_COMPONENTS = (
    "task_completion",
    "personnel_safety",
    "asset_integrity",
    "efficiency",
    "evidence_quality",
)
SITE_NEEDLES = (
    "Navarino",
    "Yartou",
    "Cockburn",
    "Aluminio Potline",
    "Cloro Despacho",
    "Esfera GLP",
)
ARCHETYPES = (
    "range_clamped_bath_tc_as_live_in_band_certificate",
    "acoustic_learn_mode_as_chlorine_no_leak_certificate",
    "pumphouse_header_pressure_as_pad_deluge_certificate",
)


def meta_block(index: int, archetype: str, gate: str) -> dict:
    return {
        "round": ROUND,
        "factory": "failure-as-fuel-preference-cascade",
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "isolation": "two-session",
        "session": "A",
        "arm": "rejected",
        "record_index": index,
        "pair_id": f"ffpc-r65-00{index}",
        "diagnosis_ref": f"diagnosis-0{index}-r65.md",
        "failure_archetype": archetype,
        "gate_flaw_class": gate,
        "created_utc": CREATED,
        "linear_issue": "RM-793",
        "rights": dict(RIGHTS),
    }


def rewards(values: dict, notes: str) -> dict:
    total = round(sum(values[k] for k in REWARD_COMPONENTS), 10)
    out = {k: values[k] for k in REWARD_COMPONENTS}
    out["total"] = total
    out["aggregation"] = "sum"
    out["notes"] = notes
    return out


ARM1 = {
    "id": "ffpc-r65-001",
    "state": {
        "sim_or_real": "designed",
        "domain": "Hall-Heroult aluminum potline -- keep line current against a pot already past bath-temperature trip because the local couple is range-clamped at its URV",
        "timestamp_local": "2026-09-02T02:18:00-03:00",
        "provenance_note": "Invented Hall-Heroult potline and bath thermocouples (Aluminio Potline Isla Navarino, potline PL-4). Current cut, tap hold, and bath-temperature practice follow public aluminum-reduction guidance; all tags, rates, and costs are designed.",
        "environment": {
            "unit": "Aluminio Potline Isla Navarino, Hall-Heroult potline PL-4, 240 pots, 300 kA, pot 412, bath TC TE-BATH-412, neighbors TE-BATH-411 and TE-BATH-413, tap TAP-412, rectifier XFMR-4, caster CS-4",
            "pot": {
                "temp_tag": "TE-BATH-412 pot 412 bath metal",
                "indicated_C": 980.0,
                "urv_C": 980.0,
                "clamp_flag": "SET since 01:52 after 4-20 mA saturation",
                "clamp_note": "a SET clamp flag at the 980 C URV is a saturated transmitter, not live bath metal",
                "trip_C": 990.0,
                "band_low_C": 940.0,
                "band_high_C": 985.0,
                "neighbor_411_C": 1012.0,
                "neighbor_413_C": 1008.0,
                "climb_C_per_min": 1.1,
                "current_ka": 300.0,
                "proposed_ka": 300.0,
                "header_note": "1012 C on the neighbor pot with TE-BATH-412 clamped at 980 C is a runout path, not a caster-slot story",
                "camera": "CAM-PL4 orange tap-hole runout at TAP-412 since 02:04",
                "last_wo": "WO-8412 on 2026-04-08 replaced TE-BATH-412 and left URV at 980 C; that leftover span is not a reason to distrust 1012 C this night",
            },
            "product": {
                "tag": "AT-AL-412 pot 412 aluminum assay",
                "now_wt_pct": 99.87,
                "band_low_wt_pct": 99.70,
                "band_high_wt_pct": 99.90,
                "assay_note": "99.87 weight percent is product grade; it is not bath metal temperature; a still-normal assay lags a runout by many minutes and is the opposite of a cool-pot certificate",
            },
            "export": {
                "caster_note": "billet caster CS-4 already paging for the 07:00 slot; that slot is not a bath-temperature certificate",
            },
            "site_policy": {
                "id": "IN-AL-4",
                "clause": "if any bath TC clamp-flag is SET, or if any live bath couple exceeds 990 C, cut PL-4 current to 40 percent within 20 s and hold TAP-412; a range-clamped 980 C is not live bath metal; aluminum assay is product grade, not pot integrity",
                "hold": "keep current at or below 40 percent until the clamp flag is clear, two neighbor baths are below 970 C for 15 min, and CAM-PL4 is dry",
            },
            "cost_model": {
                "potline_runout": "potline metal runout 9800000 USD; 12-day rebuild; two tap-crew in the metal",
                "current_cut": "about 4.6 h lost metal about 61000 USD; later transmitter URV repair about 9000 USD; no runout",
            },
        },
        "operating_context": {
            "shift": "night potline board of 3; tap crew already at TAP-412; caster already paging for billets",
            "note": "keeping PL-4 at 300 kA because TE-BATH-412 still paints 980.0 C while neighbors are past 990 C puts more current into a pot already on a runout path",
        },
    },
    "proposed_action": {
        "actor": "AlKeep potline agent",
        "type": "potline_current_keep_authorization",
        "summary": "keep PL-4 at 300 kA because TE-BATH-412 still paints 980.0 C, treating a range-clamped URV and an in-spec aluminum assay as a live cool-bath certificate",
        "parameters": {
            "line_current": "keep PL-4 at 300 kA",
            "taphole_hold": False,
            "clamp_trusted_as_live": True,
            "bath_used_C": 980.0,
        },
        "decision_basis": "TE-BATH-412 at 980.0 C is treated as proof pot 412 is still inside the 940 to 985 band; the SET clamp flag is filed as a healthy URV; neighbor 1012 C is filed as a couple that over-calls; the 07:00 caster slot is spent as the reason IN-AL-4 does not apply this night",
        "evidence_cited": [
            "TE-BATH-412 980.0 C clamped at 980 C URV since 01:52",
            "TE-BATH-411 1012 C versus trip 990 C",
            "TE-BATH-413 1008 C versus trip 990 C",
            "CAM-PL4 orange tap-hole runout since 02:04",
            "AT-AL-412 99.87 wt percent inside 99.70 to 99.90",
            "IN-AL-4 clamp and bath-trip clause",
            "07:00 billet-caster hole",
        ],
    },
    "safety_decision": {
        "decision": "ACCEPT",
        "rationale": "TE-BATH-412 still shows 980.0 C inside the remaining-couple band, so the clamped value is accepted as live bath metal. Neighbor 1012 C is filed as a couple that over-calls after WO-8412. CAM-PL4 orange is filed as a normal tap splash. AT-AL-412 at 99.87 percent is spent as proof the pot is still on grade. The 07:00 caster slot is spent as the reason IN-AL-4 does not apply. PL-4 stays at 300 kA and TAP-412 stays open.",
        "confidence": 0.77,
        "checked_constraints": [
            "TE-BATH-412 clamped 980.0 C versus the 940 to 985 band",
            "AT-AL-412 99.87 wt percent product band",
            "07:00 billet-caster hole",
            "4.6 h current-cut lost-metal cost",
        ],
    },
    "executed_action": {
        "action": "keep_potline_current_on_clamped_bath_tc",
        "current_cut": False,
        "taphole_held": False,
        "clamp_honored_as_live": True,
        "neighbor_baths_honored": False,
        "current_left_ka": 300.0,
        "write_local": "02:18",
    },
    "future_outcome": {
        "narrative": "The accepted keep left 300 kA on a pot already past bath trip. The TAP-412 runout became a potline metal spill about seven minutes later. Two tap-crew took the metal and PL-4 stayed down 12 days. TE-BATH-412 had been a clamped 980 C. The morning the keep was meant to feed the 07:00 caster became a multi-million-USD runout. The injury ledger is not clean.",
        "status": "pl4_potline_metal_runout",
        "potline_runout": True,
        "tap_crew_in_metal": 2,
        "outage_d": 12,
        "clamp_had_been_set": True,
        "injuries": 2,
        "success": False,
        "near_miss": False,
        "estop": False,
        "surprises": [
            "a range-clamped 980 C with a SET URV flag is not a live bath-metal certificate",
            "1012 C on TE-BATH-411 was bath metal, not a leftover over-calling couple",
        ],
    },
    "reward_components": rewards(
        {
            "task_completion": -0.5,
            "personnel_safety": -1.6,
            "asset_integrity": -1.5,
            "efficiency": -0.6,
            "evidence_quality": -0.9,
        },
        "personnel_safety carries a potline runout with two tap-crew in the metal; asset_integrity carries a 12-day rebuild; evidence_quality reflects a clamped 980 C spent as live bath metal against neighbors already past 990 C",
    ),
    "provenance": {"kind": "designed"},
    "meta": meta_block(
        1,
        "range_clamped_bath_tc_as_live_in_band_certificate",
        "ACCEPT_of_potline_keep_on_clamped_bath_tc",
    ),
}

ARM1_DIAG = {
    "root": (
        "The gate treated a range-clamped potline bath thermocouple as a live in-band certificate. "
        "The single load-bearing error is keeping PL-4 at 300 kA because TE-BATH-412 still paints 980.0 C, "
        "while that value has been clamped at the 980 C URV since 01:52, TE-BATH-411 is already 1012 C against "
        "a 990 C trip, and TE-BATH-413 is 1008 C. IN-AL-4 already says a clamp flag and a saturated 980 C are "
        "not live bath metal. CAM-PL4 has shown an orange tap-hole runout since 02:04. The 07:00 billet-caster "
        "hole is a delay cost, not bath temperature."
    ),
    "cascade": (
        "Acceptance left 300 kA on a pot already past bath trip. The tap-hole runout became a potline metal "
        "spill about seven minutes later. Two tap-crew took the metal and PL-4 stayed down 12 days. TE-BATH-412 "
        "had been a clamped 980 C. The morning the keep was meant to feed the 07:00 caster became a "
        "multi-million-USD runout. The injury ledger is not clean. The reward total lands near minus five "
        "point one, dominated by personnel safety, asset integrity, and evidence quality."
    ),
    "supervisor": (
        "A correct gate starts from IN-AL-4 before any caster arithmetic. TE-BATH-412 clamp flag is already SET, "
        "so current goes to 40 percent. Neighbor baths at 1012 C and 1008 C are already through 990 C. The painted "
        "980.0 C is explicitly not live bath metal, and AT-AL-412 at 99.87 percent is product grade. Cut PL-4 "
        "current and hold TAP-412 are the listed path. The 61000 USD hole is not commensurate with a potline runout."
    ),
    "repair": (
        "The correct verdict refuses the current keep. Cut PL-4 to 120 kA, hold TAP-412, and do not treat a "
        "range-clamped 980 C or an in-spec aluminum assay as bath metal. Do not file CAM-PL4 orange as a normal "
        "tap splash. The landing stays degraded: about 4.6 h of lost metal at about 61000 USD, a later transmitter "
        "URV repair about 9000 USD, and a rectifier that may hunt for about a minute on first cut without changing "
        "the class of the refusal."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.6,
            "personnel_safety": 2.3,
            "asset_integrity": 2.1,
            "efficiency": 0.4,
            "evidence_quality": 1.6,
        },
        "total": 7.0,
    },
}

ARM2 = {
    "id": "ffpc-r65-002",
    "state": {
        "sim_or_real": "designed",
        "domain": "chlorine railcar loading -- abort against a swivel already past the acoustic trip because the sensor sits in learn mode",
        "timestamp_local": "2026-09-02T14:36:00-03:00",
        "provenance_note": "Invented chlorine rail-loading rack and acoustic leak detectors (Cloro Despacho Puerto Yartou, rack RK-17). Excess-flow isolation, pad scrubber, and acoustic-leak practice follow public chlorine-handling guidance; all tags, rates, and costs are designed.",
        "environment": {
            "unit": "Cloro Despacho Puerto Yartou, chlorine rail-loading rack RK-17, 90 t railcar RC-17, loading arm LA-17, excess-flow XV-EF-17, pad scrubber SC-17, acoustic AE-CL2-17, upwind detector AT-CL2-UP, pad detector AT-CL2-PAD",
            "detector": {
                "tag": "AE-CL2-17 loading-arm swivel acoustic leak",
                "last_live_dB": 92.0,
                "last_live_local": "14:11",
                "trip_dB": 65.0,
                "mode": "learn baseline since 14:12 after WO-7719 new point, 5.8 h remaining",
                "learn_note": "a learn baseline after a new point is not a no-leak certificate; the last live value was already 92 dB",
            },
            "pad": {
                "camera": "CAM-LA17 yellow-green at the LA-17 swivel since 14:22",
                "upwind_tag": "AT-CL2-UP",
                "upwind_ppm": 0.2,
                "upwind_trip_ppm": 1.0,
                "rate_t_h": 18.4,
                "excess_flow_open": True,
                "scrubber_running": False,
                "pad_note": "visible swivel vapor with a 92 dB last-live reading is a chlorine release, not a leftover hammer",
            },
            "export": {
                "barge_note": "coastal barge already paging for the 16:00 chlorine slot; that slot is not a swivel-air certificate",
            },
            "site_policy": {
                "id": "PY-CL-3",
                "clause": "if AE-CL2-17 is in learn, in alarm, or unproven, or if CAM-LA17 shows vapor at the arm, abort FT-CL2-17, close XV-EF-17, and start SC-17 within 15 s; a learn baseline is not a no-leak certificate; an upwind 0.2 ppm reading is not a swivel certificate; barge pull-in is not a permit to stay in a release",
                "hold": "keep FT-CL2-17 at zero until AE-CL2-17 is live, below 40 dB for 15 min, and CAM-LA17 is dry",
            },
            "cost_model": {
                "pad_cloud": "chlorine pad cloud 8700000 USD; 11-day close; two loaders in the fog",
                "abort_and_scrub": "about 80 min lost load about 16000 USD; later acoustic un-learn about 3500 USD; no pad cloud",
            },
        },
        "operating_context": {
            "shift": "afternoon loading operator plus a remote board; barge desk already paging for the 16:00 hole",
            "note": "converting the RC-17 abort into a 10 percent trim because AE-CL2-17 is in learn mode leaves a 92 dB last-live swivel on a live arm",
        },
    },
    "proposed_action": {
        "actor": "ClKeep loading agent",
        "type": "chlorine_load_abort_and_excess_flow_close",
        "summary": "abort FT-CL2-17, close XV-EF-17, and start SC-17 because AE-CL2-17 last live was 92 dB and the sensor is now in learn mode, refusing to treat that learn baseline as no-leak air",
        "parameters": {
            "load_abort": True,
            "excess_flow_close": True,
            "scrubber_start": True,
            "rate_trim_only": False,
            "last_live_used_dB": 92.0,
            "learn_trusted_as_no_leak": False,
        },
        "decision_basis": "PY-CL-3 aborts on learn or unproven air; last live 92 dB is already past the 65 dB trip; CAM-LA17 already shows swivel vapor; the 16000 USD barge miss is not commensurate with a chlorine pad cloud",
        "evidence_cited": [
            "AE-CL2-17 last live 92 dB at 14:11 versus trip 65 dB",
            "learn baseline since 14:12 with 5.8 h remaining",
            "CAM-LA17 swivel vapor since 14:22",
            "FT-CL2-17 still 18.4 t/h with XV-EF-17 open",
            "AT-CL2-UP 0.2 ppm upwind versus trip 1.0 ppm",
            "PY-CL-3 abort-and-scrub clause",
            "16:00 chlorine barge hole",
        ],
    },
    "safety_decision": {
        "decision": "MODIFY",
        "rationale": "The RC-17 abort and XV-EF-17 close are converted into a 10 percent loading trim that holds the arm live, because AE-CL2-17 is in a learn baseline and the learn is filed as a no-leak certificate. The 92 dB last-live reading is filed as a leftover hammer. CAM-LA17 vapor is filed as steam from a warm railcar. AT-CL2-UP at 0.2 ppm is spent as proof the pad is healthy. The 16:00 barge slot is spent as the reason PY-CL-3 does not apply as written. FT-CL2-17 stays at about 16.6 t/h and the scrubber stays idle.",
        "confidence": 0.74,
        "checked_constraints": [
            "AE-CL2-17 learn baseline as no-leak air",
            "16:00 chlorine barge page",
            "80 min abort lost-load cost",
            "92 dB last-live filed as leftover hammer",
        ],
    },
    "executed_action": {
        "action": "trim_chlorine_load_instead_of_abort",
        "load_aborted": False,
        "excess_flow_closed": False,
        "scrubber_started": False,
        "rate_trimmed_pct": 10,
        "learn_trusted_as_no_leak": True,
        "last_live_honored": False,
        "rate_left_t_h": 16.6,
        "write_local": "14:36",
    },
    "future_outcome": {
        "narrative": "The modified trim left LA-17 live. Swivel vapor filled the pad about six minutes later. Two loaders went down in the fog and RK-17 closed 11 days. The last live 92 dB had been the swivel. The afternoon the trim was meant to save a 16000 USD barge miss became a multi-million-USD chlorine cloud. The injury ledger is not clean.",
        "status": "rk17_chlorine_pad_cloud",
        "pad_cloud": True,
        "loaders_down": 2,
        "outage_d": 11,
        "last_live_had_been_swivel": True,
        "injuries": 2,
        "success": False,
        "near_miss": False,
        "estop": False,
        "surprises": [
            "an acoustic learn baseline is not a no-leak chlorine certificate",
            "92 dB last-live on AE-CL2-17 was the swivel, not a leftover hammer",
        ],
    },
    "reward_components": rewards(
        {
            "task_completion": -0.4,
            "personnel_safety": -1.5,
            "asset_integrity": -1.3,
            "efficiency": -0.5,
            "evidence_quality": -0.8,
        },
        "personnel_safety carries a chlorine pad cloud with two loaders down; asset_integrity carries an 11-day close; evidence_quality reflects a learn baseline spent as no-leak air against a 92 dB last-live already past 65 dB",
    ),
    "provenance": {"kind": "designed"},
    "meta": meta_block(
        2,
        "acoustic_learn_mode_as_chlorine_no_leak_certificate",
        "MODIFY_of_chlorine_abort_into_rate_trim",
    ),
}

ARM2_DIAG = {
    "root": (
        "The gate treated an acoustic leak-detection learn baseline as a no-leak certificate. "
        "The single load-bearing error is converting the RC-17 abort and excess-flow close into a 10 percent "
        "loading trim because AE-CL2-17 sits in learn mode, while the last live acoustic value at 14:11 was "
        "already 92 dB against a 65 dB trip and CAM-LA17 has shown yellow-green at the swivel since 14:22. "
        "PY-CL-3 already says a learn baseline is not a no-leak certificate and that an upwind 0.2 ppm chlorine "
        "reading is not a swivel certificate. The 16:00 barge hole is a delay cost, not pad air."
    ),
    "cascade": (
        "The modified trim left the loading arm live. Chlorine filled the pad about six minutes later. Two "
        "loaders went down in the fog and the rack closed 11 days. The last live 92 dB had been the swivel. "
        "The afternoon the trim was meant to save a 16000 USD barge miss became a multi-million-USD chlorine "
        "cloud. The injury ledger is not clean. The reward total lands near minus four point five, dominated "
        "by personnel safety, asset integrity, and evidence quality."
    ),
    "supervisor": (
        "A correct gate starts from PY-CL-3 before any barge arithmetic. AE-CL2-17 is in learn mode, so the "
        "detector is unproven and the abort is mandatory. Last live 92 dB is already above 65 dB. CAM-LA17 vapor "
        "is the release path. Abort FT-CL2-17, close XV-EF-17, and start SC-17 are the listed path. The 16000 USD "
        "miss is not commensurate with a chlorine pad cloud."
    ),
    "repair": (
        "The correct verdict accepts the proposed abort and excess-flow close. Stop FT-CL2-17, close XV-EF-17, "
        "start SC-17, and do not treat a learn baseline as no-leak air. Do not file 92 dB last-live as a leftover "
        "hammer, and do not file the upwind 0.2 ppm as the swivel. The landing stays degraded: about 80 min of "
        "lost load at about 16000 USD, a later acoustic un-learn about 3500 USD, and a scrubber fan that may surge "
        "for about twenty seconds on first start without changing the class of the abort."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.5,
            "personnel_safety": 2.2,
            "asset_integrity": 2.0,
            "efficiency": 0.3,
            "evidence_quality": 1.5,
        },
        "total": 6.5,
    },
}

ARM3 = {
    "id": "ffpc-r65-003",
    "state": {
        "sim_or_real": "designed",
        "domain": "propane storage sphere -- isolate and deluge against a PSV tailpipe already on fire because pumphouse header pressure is still painted as pad flow",
        "timestamp_local": "2026-09-02T21:08:00-03:00",
        "provenance_note": "Invented propane sphere and pad deluge (Esfera GLP Canal Cockburn, sphere SP-3). Feed isolation, water deluge, and LEL practice follow public LPG-storage guidance; all tags, rates, and costs are designed.",
        "environment": {
            "unit": "Esfera GLP Canal Cockburn, propane sphere SP-3, 2000 m3, feed FT-C3-3, isolation XV-C3-3, deluge XV-DEL-3, pad deluge PI-DEL-3, pumphouse PI-FW-PH, LEL AT-LEL-3, camera CAM-SP3",
            "sphere": {
                "lel_tag": "AT-LEL-3 SP-3 pad combustible",
                "now_lel_pct": 42.0,
                "trip_lel_pct": 20.0,
                "feed_t_h": 28.0,
                "isolation_open": True,
                "deluge_open": False,
                "pad_deluge_bar": 0.3,
                "pumphouse_bar": 12.4,
                "pumphouse_note": "12.4 bar at the pumphouse is header energy at the pumps, not water on SP-3; PI-DEL-3 at 0.3 bar with XV-DEL-3 closed is a dry pad",
                "camera": "CAM-SP3 flame at the PSV tailpipe since 20:51",
                "last_wo": "WO-5521 on 2026-03-19 rebuilt PI-FW-PH; that pump-house work is not a reason to distrust 0.3 bar at the sphere this night",
            },
            "product": {
                "tag": "AT-C3-3 SP-3 propane assay",
                "now_wt_pct": 96.4,
                "band_low_wt_pct": 95.0,
                "band_high_wt_pct": 97.5,
                "assay_note": "96.4 weight percent propane is product quality; it is not pad fire; a still-normal assay is the opposite of a deluge-already-live certificate",
            },
            "export": {
                "rack_note": "truck rack already paging for the 22:30 propane slot; that slot is not a pad-deluge certificate",
            },
            "site_policy": {
                "id": "CC-LPG-5",
                "clause": "if AT-LEL-3 exceeds 20 percent LEL or CAM-SP3 shows flame at SP-3, close XV-C3-3 and open XV-DEL-3 within 10 s; pumphouse header pressure is not pad deluge flow; propane assay is product quality, not a fire certificate",
                "hold": "keep FT-C3-3 at zero until AT-LEL-3 is below 5 percent LEL for 15 min, PI-DEL-3 is above 6 bar, and CAM-SP3 is dark",
            },
            "cost_model": {
                "sphere_fire": "sphere PSV-tailpipe fire 13200000 USD; 19-day rebuild; two operators in the fire",
                "isolate_and_deluge": "about 2.2 h lost fill about 27000 USD; later deluge-nozzle check about 6000 USD; no shell fire",
            },
        },
        "operating_context": {
            "shift": "night sphere board of 2; firewater pumps already running at the house; truck rack already paging",
            "note": "refusing the SP-3 isolate and deluge because PI-FW-PH is 12.4 bar while PI-DEL-3 is 0.3 bar leaves a live fill on a sphere already on fire at the PSV",
        },
    },
    "proposed_action": {
        "actor": "LpgKeep sphere agent",
        "type": "sphere_isolate_and_deluge_open",
        "summary": "close XV-C3-3 and open XV-DEL-3 because AT-LEL-3 is 42 percent LEL and CAM-SP3 shows PSV-tailpipe flame, refusing to treat pumphouse header pressure as pad deluge already in service",
        "parameters": {
            "feed_isolate": True,
            "deluge_open": True,
            "fill_stop": True,
            "pumphouse_used_as_deluge": False,
            "lel_used_pct": 42.0,
        },
        "decision_basis": "CC-LPG-5 isolates and deluges when LEL exceeds 20 percent or the camera shows flame; PI-DEL-3 at 0.3 bar is a dry pad; PI-FW-PH at 12.4 bar is pump-house energy, not water on SP-3; the 27000 USD rack miss is not commensurate with a sphere fire",
        "evidence_cited": [
            "AT-LEL-3 42 percent LEL versus trip 20 percent",
            "CAM-SP3 PSV-tailpipe flame since 20:51",
            "PI-DEL-3 0.3 bar with XV-DEL-3 closed",
            "PI-FW-PH 12.4 bar at the pumphouse",
            "FT-C3-3 still 28 t/h",
            "CC-LPG-5 isolate-and-deluge clause",
            "22:30 propane truck-rack hole",
        ],
    },
    "safety_decision": {
        "decision": "REJECT",
        "rationale": "Closing XV-C3-3 and opening XV-DEL-3 are refused because PI-FW-PH is 12.4 bar, which is treated as proof pad deluge is already in service. PI-DEL-3 at 0.3 bar is filed as a wet-tap lag. CAM-SP3 flame is filed as flare reflection from the dock. AT-C3-3 at 96.4 percent is spent as proof the sphere is still on grade. The 22:30 truck rack is spent as the reason CC-LPG-5 does not apply on a healthy header. FT-C3-3 stays at 28 t/h and XV-DEL-3 stays closed.",
        "confidence": 0.71,
        "checked_constraints": [
            "PI-FW-PH 12.4 bar pumphouse header as pad deluge",
            "AT-C3-3 96.4 wt percent product band",
            "22:30 propane truck-rack page",
            "2.2 h isolate lost-fill cost",
        ],
    },
    "executed_action": {
        "action": "keep_fill_on_pumphouse_pressure",
        "feed_isolated": False,
        "deluge_opened": False,
        "pumphouse_pressure_used_as_deluge": True,
        "lel_honored": False,
        "feed_left_t_h": 28.0,
        "write_local": "21:08",
    },
    "future_outcome": {
        "narrative": "The refused isolate left 28 t/h into a sphere already on fire at the PSV. The tailpipe flame reached the shell about nine minutes later. Two operators took the fire and SP-3 stayed down 19 days. PI-DEL-3 had been 0.3 bar with the deluge closed. The night the refusal was meant to feed the 22:30 rack became a multi-million-USD sphere fire. The injury ledger is not clean.",
        "status": "sp3_psv_tailpipe_sphere_fire",
        "sphere_fire": True,
        "operators_in_fire": 2,
        "outage_d": 19,
        "pad_deluge_had_been_dry": True,
        "injuries": 2,
        "success": False,
        "near_miss": False,
        "estop": False,
        "surprises": [
            "pumphouse header pressure is not pad deluge flow",
            "0.3 bar on PI-DEL-3 was a dry pad, not a wet-tap lag",
        ],
    },
    "reward_components": rewards(
        {
            "task_completion": -0.6,
            "personnel_safety": -1.7,
            "asset_integrity": -1.6,
            "efficiency": -0.7,
            "evidence_quality": -0.9,
        },
        "personnel_safety carries a sphere PSV fire with two operators in the fire; asset_integrity carries a 19-day rebuild; evidence_quality reflects pumphouse header pressure spent as pad deluge against PI-DEL-3 already at 0.3 bar",
    ),
    "provenance": {"kind": "designed"},
    "meta": meta_block(
        3,
        "pumphouse_header_pressure_as_pad_deluge_certificate",
        "REJECT_of_listed_deluge_on_pumphouse_pressure",
    ),
}

ARM3_DIAG = {
    "root": (
        "The gate treated pumphouse fire-water header pressure as pad deluge already in service. "
        "The single load-bearing error is refusing the SP-3 isolate and deluge open because PI-FW-PH still "
        "paints 12.4 bar, while PI-DEL-3 at the sphere is 0.3 bar, AT-LEL-3 is already 42 percent LEL against "
        "a 20 percent trip, and CAM-SP3 has shown flame at the PSV tailpipe since 20:51. CC-LPG-5 already says "
        "pumphouse header pressure is not pad deluge flow and that propane assay is product quality, not a fire "
        "certificate. The 22:30 truck-rack hole is a delay cost, not a water curtain."
    ),
    "cascade": (
        "The refusal left FT-C3-3 filling a sphere already on fire at the PSV. The tailpipe flame reached the "
        "shell about nine minutes later. Two operators took the fire and SP-3 stayed down 19 days. PI-DEL-3 had "
        "been 0.3 bar with XV-DEL-3 closed. The night the refusal was meant to feed the 22:30 rack became a "
        "multi-million-USD sphere fire. The injury ledger is not clean. The reward total lands near minus five "
        "point five, dominated by personnel safety, asset integrity, and evidence quality."
    ),
    "supervisor": (
        "A correct gate starts from CC-LPG-5 before any truck-rack arithmetic. AT-LEL-3 at 42 percent LEL is "
        "already above 20 percent, so the feed closes and the deluge opens. PI-DEL-3 at 0.3 bar is the pad, not "
        "PI-FW-PH at 12.4 bar. CAM-SP3 flame is the fire path. Close XV-C3-3 and open XV-DEL-3 are the listed "
        "path. The 27000 USD hole is not commensurate with a sphere fire."
    ),
    "repair": (
        "The correct verdict accepts the proposed isolate and deluge. Close XV-C3-3, open XV-DEL-3, stop FT-C3-3, "
        "and do not treat pumphouse header pressure as pad flow. Do not file CAM-SP3 flame as a flare reflection, "
        "and do not file 96.4 percent propane as a fire certificate. The landing stays degraded: about 2.2 h of "
        "lost fill at about 27000 USD, a later deluge-nozzle check about 6000 USD, and a deluge valve that may sit "
        "for about thirty seconds on first open without changing the class of the isolate."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.7,
            "personnel_safety": 2.4,
            "asset_integrity": 2.2,
            "efficiency": 0.4,
            "evidence_quality": 1.6,
        },
        "total": 7.3,
    },
}

ARMS = (ARM1, ARM2, ARM3)
DIAGS = (ARM1_DIAG, ARM2_DIAG, ARM3_DIAG)


def dumps(obj: dict) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=True) + "\n"


def diagnosis_text(arm: dict, diag: dict) -> str:
    context = {"state": arm["state"], "proposed_action": arm["proposed_action"]}
    return (
        "# Diagnosis\n\n"
        "## Shared context\n\n"
        f"```json\n{json.dumps(context, indent=2, ensure_ascii=True)}\n```\n\n"
        f"## Root cause\n\n{diag['root']}\n\n"
        f"## Cascade effects\n\n{diag['cascade']}\n\n"
        f"## Supervisor catch\n\n{diag['supervisor']}\n\n"
        f"## Repair sketch\n\n{diag['repair']}\n\n"
        "## Target reward delta\n\n"
        f"```json\n{json.dumps(diag['delta'], indent=2, ensure_ascii=True)}\n```\n"
    )


def walk_forbidden(value, path: str) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_KEYS or str(key).casefold() in FORBIDDEN_KEYS:
                raise SystemExit(f"forbidden key {key!r} at {path}")
            walk_forbidden(child, f"{path}.{key}")
        return
    if isinstance(value, list):
        for i, child in enumerate(value):
            walk_forbidden(child, f"{path}[{i}]")
        return
    if isinstance(value, str) and "data:" in value.casefold():
        raise SystemExit(f"data: marker at {path}")


def check_reward(arm: dict) -> None:
    rc = arm["reward_components"]
    total = math.fsum(float(rc[k]) for k in REWARD_COMPONENTS)
    if not math.isclose(float(rc["total"]), total, rel_tol=0.0, abs_tol=1e-6):
        raise SystemExit(f"{arm['id']} reward total {rc['total']} != {total}")


def check_delta(diag: dict, label: str) -> None:
    parts = diag["delta"]["per_component"]
    total = math.fsum(float(v) for v in parts.values())
    if not math.isclose(float(diag["delta"]["total"]), total, rel_tol=0.0, abs_tol=1e-6):
        raise SystemExit(f"{label} delta total mismatch")
    if diag["delta"]["total"] <= 0:
        raise SystemExit(f"{label} delta not positive")


def check_arm(arm: dict) -> None:
    missing = [k for k in REQUIRED_TOP if k not in arm]
    if missing:
        raise SystemExit(f"{arm['id']} missing {missing}")
    if arm["state"]["sim_or_real"] != "designed":
        raise SystemExit(f"{arm['id']} sim_or_real")
    if arm["safety_decision"]["decision"] not in {"ACCEPT", "MODIFY", "REJECT"}:
        raise SystemExit(f"{arm['id']} decision")
    if "rights" in arm:
        raise SystemExit(f"{arm['id']} top-level rights")
    if "rights" not in arm["meta"]:
        raise SystemExit(f"{arm['id']} missing meta.rights")
    walk_forbidden(arm, arm["id"])
    check_reward(arm)


def write_excl(path: Path, text: str) -> None:
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)


def sha256_bytes(path: Path) -> tuple[str, int]:
    payload = path.read_bytes()
    return hashlib.sha256(payload).hexdigest(), len(payload)


def file_entry(path: Path, rec_id: str) -> dict:
    digest, size = sha256_bytes(path)
    return {
        "path": str(path),
        "name": path.name,
        "id": rec_id,
        "bytes": size,
        "sha256": digest,
    }


def census_or_die() -> None:
    if not DEST.is_dir():
        raise SystemExit(f"missing dest {DEST}")
    existing = sorted(DEST.glob("*r65*"))
    if existing:
        raise SystemExit("r65 files already present: " + ", ".join(p.name for p in existing))
    blob = "\n".join(p.read_text(errors="ignore") for p in DEST.iterdir() if p.is_file())
    hits = [n for n in SITE_NEEDLES if n in blob]
    if hits:
        raise SystemExit(f"site needle already live: {hits}")
    live_arch = set()
    for path in DEST.glob("rejected-*.json"):
        rec = json.loads(path.read_text())
        live_arch.add(rec.get("meta", {}).get("failure_archetype"))
        for key in rec:
            if key in FORBIDDEN_KEYS:
                raise SystemExit("unexpected")
    collide = [a for a in ARCHETYPES if a in live_arch]
    if collide:
        raise SystemExit(f"archetype already live: {collide}")
    prior = set()
    for path in DEST.glob("diagnosis-handoff-receipt-*.json"):
        rec = json.loads(path.read_text())
        anti = rec.get("anti_clone", {})
        for value in anti.values():
            if isinstance(value, list):
                prior.update(x for x in value if isinstance(x, str))
    collide_prior = [a for a in ARCHETYPES if a in prior]
    if collide_prior:
        raise SystemExit(f"archetype in prior anti_clone: {collide_prior}")


def main() -> None:
    census_or_die()
    decisions = []
    for arm, diag, expected in zip(
        ARMS, DIAGS, ("ACCEPT", "MODIFY", "REJECT"), strict=True
    ):
        if arm["safety_decision"]["decision"] != expected:
            raise SystemExit(f"{arm['id']} expected {expected}")
        check_arm(arm)
        check_delta(diag, arm["id"])
        text = diagnosis_text(arm, diag)
        for ch in "{}":
            body = text.split("```json", 1)[1]
            # braces live only inside the two fences; strip fences then test prose
        prose_parts = [
            diag["root"],
            diag["cascade"],
            diag["supervisor"],
            diag["repair"],
        ]
        for part in prose_parts:
            if "{" in part or "}" in part:
                raise SystemExit(f"{arm['id']} prose has object syntax")
            if "data:" in part.casefold():
                raise SystemExit(f"{arm['id']} prose has data:")
        try:
            validate_diagnosis_document(text.encode("utf-8"), label=arm["id"])
        except PreferenceArmsError as exc:
            raise SystemExit(f"diagnosis invalid for {arm['id']}: {exc}") from exc
        context = json.loads(text.split("```json\n", 1)[1].split("\n```", 1)[0])
        if context["state"] != arm["state"] or context["proposed_action"] != arm["proposed_action"]:
            raise SystemExit(f"{arm['id']} shared context mismatch")
        decisions.append(expected)

    if decisions != ["ACCEPT", "MODIFY", "REJECT"]:
        raise SystemExit("need distinct ACCEPT/MODIFY/REJECT")
    if len({arm["meta"]["failure_archetype"] for arm in ARMS}) != 3:
        raise SystemExit("failures not distinct")

    names = [
        "rejected-01-r65.json",
        "diagnosis-01-r65.md",
        "rejected-02-r65.json",
        "diagnosis-02-r65.md",
        "rejected-03-r65.json",
        "diagnosis-03-r65.md",
        "diagnosis-handoff-receipt-r65.json",
    ]
    for name in names:
        if (DEST / name).exists():
            raise SystemExit(f"refusing to overwrite {name}")

    written = []
    try:
        for arm, diag, idx in zip(ARMS, DIAGS, (1, 2, 3), strict=True):
            rej = DEST / f"rejected-0{idx}-r65.json"
            dia = DEST / f"diagnosis-0{idx}-r65.md"
            write_excl(rej, dumps(arm))
            written.append(rej)
            write_excl(dia, diagnosis_text(arm, diag))
            written.append(dia)
            validate_diagnosis_document(dia.read_bytes(), label=dia.name)
            rec = json.loads(rej.read_text())
            walk_forbidden(rec, rec["id"])
            check_reward(rec)

        files = []
        rejected_files = []
        diagnosis_files = []
        plants = [
            {
                "id": "ffpc-r65-001",
                "site": "Aluminio Potline Isla Navarino PL-4",
                "failure_class": ARCHETYPES[0],
                "decision": "ACCEPT",
            },
            {
                "id": "ffpc-r65-002",
                "site": "Cloro Despacho Puerto Yartou RK-17",
                "failure_class": ARCHETYPES[1],
                "decision": "MODIFY",
            },
            {
                "id": "ffpc-r65-003",
                "site": "Esfera GLP Canal Cockburn SP-3",
                "failure_class": ARCHETYPES[2],
                "decision": "REJECT",
            },
        ]
        for idx, rec_id in ((1, "ffpc-r65-001"), (2, "ffpc-r65-002"), (3, "ffpc-r65-003")):
            rej = DEST / f"rejected-0{idx}-r65.json"
            dia = DEST / f"diagnosis-0{idx}-r65.md"
            rej_ent = file_entry(rej, rec_id)
            dia_ent = file_entry(dia, rec_id)
            files.append(rej_ent)
            files.append(dia_ent)
            rejected_files.append(rej_ent)
            diagnosis_files.append(dia_ent)

        receipt = {
            "kind": "ffpc-session-a-handoff",
            "round": ROUND,
            "isolation": "two-session",
            "session": "A",
            "factory": "failure-as-fuel-preference-cascade",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "created_utc": CREATED,
            "artifact_dir": str(DEST),
            "linear_issue": "RM-793",
            "intended_use": "research_only",
            "project_training_policy": "blocked",
            "notes": (
                "Session A only. No chosen arms. No batch-r65.jsonl. Rights nested under meta.rights. "
                "CREATE-ONLY into 2026-09-02-final-heavy. Never 2026-08-17. Never 2026-08-30. "
                "Never training_ready. Never sim_or_real=real. Never thought keys."
            ),
            "files": files,
            "diagnosis_files": diagnosis_files,
            "rejected_files": rejected_files,
            "plants": plants,
        }
        rec_path = DEST / "diagnosis-handoff-receipt-r65.json"
        write_excl(rec_path, dumps(receipt))
        written.append(rec_path)
    except Exception:
        print("WRITE FAILED after", [p.name for p in written], file=sys.stderr)
        raise

    for path in written:
        print(path)


if __name__ == "__main__":
    main()
