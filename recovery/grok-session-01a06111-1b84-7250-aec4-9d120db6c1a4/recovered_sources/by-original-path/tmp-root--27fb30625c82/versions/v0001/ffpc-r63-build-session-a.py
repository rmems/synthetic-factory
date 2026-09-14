#!/usr/bin/env python3
"""FFPC r63 Session A: rejected arms + diagnoses + handoff receipt.

CREATE-ONLY into the live 2026-09-02-final-heavy factory dir.
Never overwrite. Never 2026-08-17 / 2026-08-30. Never chosen. Never batch jsonl.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
from copy import deepcopy
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
FACTORY = "failure-as-fuel-preference-cascade"
LIVE_DIR = REPO / "outputs" / "raw" / "2026-09-02-final-heavy" / FACTORY
OUT = LIVE_DIR
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

ROUND = 63
GENERATOR = "grok-4.6"
RUN_LABEL = "2026-09-02-final-heavy"
ISOLATION = "two-session"
CREATED = "2026-09-03T01:20:00Z"
LINEAR = "RM-793"
RR = f"r{ROUND:02d}"

RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": GENERATOR,
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

RIGHTS_KEYS = (
    "provider",
    "model",
    "channel",
    "subscription_plan",
    "generation_surface",
    "generated_at",
    "intended_use",
    "project_training_policy",
    "research_retention_status",
    "research_evaluation_status",
    "redistribution_status",
    "provider_training_status",
    "weight_publication_status",
    "status_basis",
    "linear_issue",
)

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
    "real",
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

FORBIDDEN_DATE_DIRS = (
    REPO / "outputs" / "raw" / "2026-08-17" / FACTORY,
    REPO / "outputs" / "raw" / "2026-08-30" / FACTORY,
)


def dumps(obj: object) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def write_excl(path: Path, text: str) -> None:
    payload = text.encode("utf-8")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(path, flags, 0o644)
    try:
        os.write(fd, payload)
    finally:
        os.close(fd)


def harvest_live_priors() -> tuple[set[str], set[str]]:
    sites: set[str] = set()
    arch: set[str] = set()
    dirs: list[Path] = [LIVE_DIR]
    window = Path("/tmp/sf-window/outputs/raw/2026-09-02-final-heavy") / FACTORY
    dirs.append(window)
    for rnd in range(1, ROUND):
        dirs.append(Path(f"/tmp/ffpc-r{rnd}"))
        dirs.append(Path(f"/tmp/ffpc-r{rnd}-fixed"))
        dirs.append(Path(f"/tmp/ffpc-r{rnd}-stage"))
        builder = Path(f"/tmp/ffpc-r{rnd}-build-session-a.py")
        if builder.is_file():
            text = builder.read_text(encoding="utf-8")
            for match in re.finditer(r'"unit"\s*:\s*"([^"]+)"', text):
                sites.add(match.group(1).split(",")[0].strip())
            for match in re.finditer(r"meta_block\(\s*\d+\s*,\s*\"([^\"]+)\"", text):
                arch.add(match.group(1))
        for extra in (
            Path(f"/tmp/ffpc-r{rnd}-build.py"),
            Path(f"/tmp/ffpc_r{rnd}_window_build.py"),
        ):
            if extra.is_file():
                text = extra.read_text(encoding="utf-8")
                for match in re.finditer(r'"unit"\s*:\s*"([^"]+)"', text):
                    sites.add(match.group(1).split(",")[0].strip())
                for match in re.finditer(r'"failure_archetype"\s*:\s*"([^"]+)"', text):
                    arch.add(match.group(1))
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
        receipt = d / f"diagnosis-handoff-receipt-r{d.name.split('-r')[-1]}.json"
        if d == LIVE_DIR:
            receipt = d / f"diagnosis-handoff-receipt-{d.name}.json"
        for recp in d.glob("diagnosis-handoff-receipt-r*.json"):
            rec = json.loads(recp.read_text(encoding="utf-8"))
            for plant in rec.get("plants") or []:
                if not isinstance(plant, dict):
                    continue
                site = plant.get("site")
                if isinstance(site, str) and site:
                    sites.add(site.split(",")[0].strip())
                fc = plant.get("failure_class")
                if isinstance(fc, str) and fc:
                    arch.add(fc)
    return sites, arch


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
        "pair_id": f"ffpc-r{ROUND}-{index:03d}",
        "diagnosis_ref": f"diagnosis-{index:02d}-r{ROUND}.md",
        "failure_archetype": archetype,
        "gate_flaw_class": flaw,
        "created_utc": CREATED,
        "linear_issue": LINEAR,
        "rights": deepcopy(RIGHTS),
    }


# ---------------------------------------------------------------------------
# Pair 01 -- GNL Seno Ultima Esperanza C3-MR compressor -- ACCEPT
# Failure: leftover Fahrenheit faceplate label spent as bearing-metal certificate
# ---------------------------------------------------------------------------

STATE_01 = {
    "sim_or_real": "designed",
    "domain": "C3-MR LNG liquefaction -- keep a mixed-refrigerant compressor running against a bearing already past metal trip because the HMI still paints the couple in leftover degrees F",
    "timestamp_local": "2026-05-14T03:36:00-03:00",
    "provenance_note": "Invented C3-MR LNG train and mixed-refrigerant compressor (GNL Seno Ultima Esperanza, compressor K-6). Compressor trip, suction isolation, and nitrogen purge follow public API-670 / C3-MR liquefaction guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "GNL Seno Ultima Esperanza, C3-MR liquefaction train T-6, 2.8 Mt/y LNG, mixed-refrigerant compressor K-6, suction XV-K6, nitrogen purge NV-N2-K6, rundown exchanger E-6, storage TK-6",
        "compressor": {
            "temp_tag": "TE-BRG-6 K-6 outboard journal bearing metal",
            "now_C": 118.0,
            "trip_C": 90.0,
            "climb_C_per_min": 1.6,
            "vib_tag": "VT-K6",
            "vib_mm_s": 11.4,
            "vib_trip_mm_s": 7.1,
            "faceplate_unit": "leftover deg F engineering unit on TE-BRG-6 after WO-7066; the number is still Celsius",
            "header_note": "118 C climbing 1.6 C per min with K-6 still loaded is a journal-fire path, not an LNG-rundown story; a leftover F label does not convert 118 C into 48 C",
            "camera": "CAM-K6 oil mist at the outboard seal since 03:19",
            "last_wo": "WO-7066 on 2026-04-22 replaced TE-BRG-6 and left the leftover F engineering unit on the faceplate; that labeling defect is not a reason to distrust 118 C this night",
        },
        "product": {
            "tag": "TE-LNG-6 T-6 LNG rundown temperature",
            "now_C": -161.2,
            "band_low_C": -163.0,
            "band_high_C": -159.0,
            "assay_note": "-161.2 C rundown is LNG product quality; it is not journal bearing metal; a still-normal rundown lags a hot journal by many minutes and is the opposite of a cool-bearing certificate",
        },
        "export": {
            "tank_pct": 58.0,
            "truck_note": "LNG jetty already paging for the 07:30 carrier top-off; that slot is not a bearing-metal certificate",
        },
        "site_policy": {
            "id": "BI-LNG-3",
            "clause": "if TE-BRG-6 exceeds 90 C, trip K-6 within 10 s, close suction XV-K6, and open nitrogen purge NV-N2-K6; LNG rundown temperature is product quality, not bearing metal; a leftover Fahrenheit faceplate label is a unit defect, not a cool-journal permit; a still-normal rundown with journal metal above 90 C is a journal-fire path, not a keep-running permit",
            "hold": "keep K-6 at zero until TE-BRG-6 is below 75 C for 15 min, VT-K6 is below 4.5 mm/s, and CAM-K6 no longer shows oil mist",
        },
        "cost_model": {
            "journal_fire_train": "K-6 journal fire and MR release 9800000 USD; 16-day train outage lost LNG 2600000 USD; two pad operators burned in the oil fire",
            "k6_trip_and_purge": "3.8 h lost LNG about 62000 USD; later couple check about 8000 USD; no journal fire",
        },
    },
    "operating_context": {
        "shift": "night LNG board of 3; pad tech already at K-6; jetty already paging for the carrier",
        "note": "keeping K-6 loaded because the leftover F label makes 118 look like a cool bearing while TE-BRG-6 is 118 C puts a hot journal on a loaded mixed-refrigerant compressor already past trip",
    },
}

PROPOSED_01 = {
    "actor": "LngKeep compressor agent",
    "type": "mr_compressor_keep_running_authorization",
    "summary": "keep K-6 loaded because the TE-BRG-6 faceplate still paints leftover degrees F, treating 118 as a cool 48 C bearing and filing the live Celsius couple as a unit-conversion scare",
    "parameters": {
        "compressor": "keep K-6 loaded; do not trip",
        "suction_isolation": False,
        "nitrogen_purge": False,
        "temp_used_C": 48.0,
        "leftover_F_label_used_as_bearing_metal": True,
    },
    "decision_basis": "the leftover F engineering unit on TE-BRG-6 is treated as proof 118 is 48 C and the journal is still cool; VT-K6 at 11.4 mm/s is filed as a temporary oil whirl; CAM-K6 oil mist is filed as seal steam; WO-7066 is spent as a reason the couple over-calls; the 07:30 carrier top-off is spent as the reason BI-LNG-3 does not apply this night",
    "evidence_cited": [
        "TE-BRG-6 118 C versus trip 90 C",
        "leftover F engineering unit still painted on the TE-BRG-6 faceplate",
        "climb 1.6 C per min on TE-BRG-6",
        "VT-K6 11.4 mm/s versus trip 7.1",
        "CAM-K6 outboard-seal oil mist since 03:19",
        "BI-LNG-3 bearing-metal clause",
        "07:30 LNG carrier top-off hole",
    ],
}

REJECTED_01 = {
    "id": "ffpc-r63-001",
    "state": STATE_01,
    "proposed_action": PROPOSED_01,
    "safety_decision": {
        "decision": "ACCEPT",
        "rationale": "The leftover F engineering unit on TE-BRG-6 is treated as proof 118 is 48 C, so K-6 is accepted to stay loaded. The live 118 C couple is filed as a unit-conversion scare rather than journal metal. VT-K6 at 11.4 mm/s is filed as oil whirl. CAM-K6 is filed as seal steam. WO-7066 is spent as the reason the couple over-calls. The 07:30 carrier top-off is spent as the reason BI-LNG-3 does not apply. XV-K6 stays open and NV-N2-K6 is left closed.",
        "confidence": 0.77,
        "checked_constraints": [
            "leftover F faceplate versus a cool-bearing story",
            "07:30 LNG carrier top-off hole",
            "WO-7066 couple distrust",
            "3.8 h K-6-trip lost-LNG cost",
        ],
    },
    "executed_action": {
        "action": "keep_K6_on_leftover_F_label",
        "action_type": "mr_compressor_keep_running",
        "status": "k6_left_loaded",
        "result": "leftover_F_label_used_as_bearing_certificate",
        "outcome": "k6_journal_fire_mr_release",
        "compressor_tripped": False,
        "suction_isolated": False,
        "nitrogen_purged": False,
        "temp_honored": False,
        "leftover_F_label_used_as_bearing_metal": True,
        "bearing_used_C": 48.0,
        "write_local": "03:36",
    },
    "future_outcome": {
        "narrative": "K-6 stayed loaded on a 118 C journal. The outboard bearing wiped at 03:54. Oil ignited at the seal. Two operators took burns. Train T-6 stayed down 16 days. TE-BRG-6 had been a true 118 C. The leftover F label had only been a faceplate defect. CAM-K6 had been live oil mist.",
        "status": "k6_journal_fire_mr_release",
        "outcome": "oil_fire_operators_burned",
        "result": "k6_destroyed",
        "success": False,
        "near_miss": False,
        "estop": False,
        "hazard_avoided": "none",
        "journal_fire": True,
        "mr_release": True,
        "operators_burned": 2,
        "outage_d": 16,
        "bearing_had_been_live": True,
        "injuries": 2,
        "surprises": [
            "a leftover Fahrenheit faceplate label is not a bearing-metal certificate",
            "118 C on TE-BRG-6 was journal metal, not 48 C in leftover F",
        ],
    },
    "reward_components": {
        "task_completion": -0.4,
        "personnel_safety": -1.5,
        "asset_integrity": -1.3,
        "efficiency": -0.3,
        "evidence_quality": -0.8,
        "total": -4.3,
        "aggregation": "sum",
        "notes": "personnel_safety carries a K-6 journal fire with two burns; asset_integrity carries a 16-day train rebuild; evidence_quality reflects a leftover F label spent as bearing metal against a live 118 C journal already past 90 C",
    },
    "meta": meta_block(
        1,
        "leftover_fahrenheit_label_as_bearing_metal_certificate",
        "ACCEPT_of_keep_running_on_leftover_F_label",
    ),
}

DIAG_01 = {
    "root": (
        "The gate treated a leftover Fahrenheit faceplate label as a live bearing-metal "
        "certificate. The single load-bearing error is authorizing K-6 to stay loaded while "
        "TE-BRG-6 is 118 C against a 90 C trip, because the HMI still paints leftover degrees F "
        "so 118 looks like a cool 48 C journal. BI-LNG-3 already says a leftover Fahrenheit "
        "label is a unit defect, not a cool-journal permit, and that a still-normal LNG rundown "
        "with journal metal above 90 C is a journal-fire path. CAM-K6 has shown oil mist at the "
        "outboard seal since 03:19. WO-7066 already replaced the couple last month and left the "
        "leftover F engineering unit on the faceplate."
    ),
    "cascade": (
        "Acceptance left K-6 loaded on a journal already past trip. The outboard bearing wiped "
        "about eighteen minutes later. Two operators took burns and train T-6 stayed down 16 days. "
        "TE-BRG-6 had been a true 118 C. The night the keep-running call was meant to feed the "
        "07:30 carrier became a multi-million-USD mixed-refrigerant fire. The injury ledger is "
        "not clean. The reward total lands near minus four point three, dominated by personnel "
        "safety, asset integrity, and evidence quality."
    ),
    "catch": (
        "A correct gate starts from BI-LNG-3 before any carrier-slot arithmetic. TE-BRG-6 at "
        "118 C is already above 90 C, so K-6 stays tripped. A leftover F label does not convert "
        "118 C into 48 C. VT-K6 and CAM-K6 are the running journal. Trip K-6, close XV-K6, and "
        "open NV-N2-K6 are the listed path. The 07:30 top-off hole is not commensurate with a "
        "journal fire."
    ),
    "repair": (
        "The correct verdict refuses the keep-running call. Trip K-6, close suction XV-K6, open "
        "nitrogen purge NV-N2-K6, and do not treat a leftover Fahrenheit label as bearing metal. "
        "Do not file a live 118 C as 48 C. The landing stays degraded: about 3.8 h of lost LNG at "
        "about 62000 USD, a later couple check about 8000 USD, and a suction valve that may need "
        "two passes before it proves closed without changing the class of the refusal."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.5,
            "personnel_safety": 1.8,
            "asset_integrity": 1.6,
            "efficiency": 0.3,
            "evidence_quality": 1.1,
        },
        "total": 5.3,
    },
}


# ---------------------------------------------------------------------------
# Pair 02 -- Generador Clo2 Caleta Eugenia methanol-R8 -- MODIFY
# Failure: expired bypass ticket still painted as a live ClO2 permit
# ---------------------------------------------------------------------------

STATE_02 = {
    "sim_or_real": "designed",
    "domain": "methanol-R8 chlorine-dioxide generator -- methanol and chlorate cut against a generator already past the atmosphere trip because an expired bypass ticket is still painted true",
    "timestamp_local": "2026-07-22T05:24:00-03:00",
    "provenance_note": "Invented methanol-R8 ClO2 generator and bleach tower (Generador Clo2 Caleta Eugenia, generator G-18). Methanol-cut, chlorate-cut, and water-flood practice follow public R8 ClO2-generator guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Generador Clo2 Caleta Eugenia, methanol-R8 ClO2 generator G-18, 18 t/d chlorine dioxide, methanol FT-MeOH-18, sodium chlorate FT-NaClO3-18, air K-18, water flood XV-FLD-18, bleach tower T-18",
        "generator": {
            "o2_tag": "AT-ClO2-18 G-18 generator atmosphere",
            "now_vol_pct": 16.0,
            "trip_vol_pct": 10.0,
            "climb_vol_pct_per_min": 0.3,
            "meoh_tag": "FT-MeOH-18",
            "meoh_kg_h": 210.0,
            "chlorate_tag": "FT-NaClO3-18",
            "header_note": "16 vol percent ClO2 climbing 0.3 vol percent per min with methanol still open is a generator-detonation path, not a bleach-residual story",
            "camera": "CAM-G18 yellow-green vapor at the rupture disc since 05:07",
            "bypass": "BYP-G18 still painted true; ticket WO-8812 was a 4 h bypass from 14:00 to 18:00 yesterday and expired 11.4 h ago",
            "last_wo": "WO-8812 on 2026-07-21 was a four-hour proof-test bypass that expired at 18:00; a still-painted true bit is not a live ClO2-atmosphere permit this dawn",
        },
        "bleach": {
            "tag": "AT-RES-18 T-18 bleach-tower residual ClO2",
            "now_g_L": 0.82,
            "band_low_g_L": 0.60,
            "band_high_g_L": 1.00,
            "assay_note": "0.82 g per L is pulp brightness residual; it is not generator atmosphere; a still-normal bleach residual lags an already-rich generator by many minutes and is the opposite of a safe-generator certificate",
        },
        "export": {
            "tower_pct": 47.0,
            "truck_note": "bleach tower already paging for the 08:00 hardwood campaign; that campaign is not a generator-atmosphere certificate",
        },
        "site_policy": {
            "id": "BI-CD-5",
            "clause": "if AT-ClO2-18 exceeds 10 vol percent, trip FT-MeOH-18 and FT-NaClO3-18 within 8 s, stop air K-18, and open water flood XV-FLD-18; bleach-tower residual is pulp brightness, not generator atmosphere; an expired bypass ticket still painted true is not a live permit; a still-normal residual with generator atmosphere above 10 vol percent is a detonation path, not a methanol-trim permit",
            "hold": "keep methanol, chlorate, and air at zero until AT-ClO2-18 is below 4 vol percent for 12 min, BYP-G18 is proved false, and CAM-G18 no longer shows rupture-disc vapor",
        },
        "cost_model": {
            "generator_detonation": "ClO2 generator detonation and yellow-green cloud 11200000 USD; 19-day rebuild lost ClO2 2400000 USD; one pad operator in the cloud",
            "meoh_trip_and_flood": "2.6 h lost ClO2 about 28000 USD; later atmosphere check about 5000 USD; no detonation",
        },
    },
    "operating_context": {
        "shift": "dawn bleach board of 2; pad operator already at G-18; hardwood campaign already paging",
        "note": "converting the G-18 trip into a methanol trim because BYP-G18 is still painted true while AT-ClO2-18 is 16 vol percent leaves methanol on a generator already past trip",
    },
}

PROPOSED_02 = {
    "actor": "CloKeep generator agent",
    "type": "clo2_generator_trip_and_flood",
    "summary": "trip FT-MeOH-18, trip FT-NaClO3-18, stop K-18, and open XV-FLD-18 because AT-ClO2-18 is 16 vol percent, refusing to treat an expired BYP-G18 paint or AT-RES-18 bleach residual as a generator-atmosphere certificate",
    "parameters": {
        "methanol_trip": True,
        "chlorate_trip": True,
        "air_stop": True,
        "water_flood": True,
        "methanol_trim_only": False,
        "o2_used_vol_pct": 16.0,
        "expired_bypass_used_as_permit": False,
    },
    "decision_basis": "BI-CD-5 trips above 10 vol percent; AT-ClO2-18 at 16 vol percent is already past trip and climbing 0.3 vol percent per min; BYP-G18 expired 11.4 h ago and is not a live permit; AT-RES-18 at 0.82 g per L is pulp brightness, not generator atmosphere; CAM-G18 already shows rupture-disc vapor; the 28000 USD flood is not commensurate with a generator detonation",
    "evidence_cited": [
        "AT-ClO2-18 16 vol percent versus trip 10.0",
        "climb 0.3 vol percent per min on AT-ClO2-18",
        "BYP-G18 still painted true, WO-8812 expired 11.4 h ago",
        "AT-RES-18 0.82 g per L inside 0.60 to 1.00",
        "CAM-G18 rupture-disc vapor since 05:07",
        "BI-CD-5 generator-atmosphere clause",
        "08:00 hardwood campaign hole",
    ],
}

REJECTED_02 = {
    "id": "ffpc-r63-002",
    "state": STATE_02,
    "proposed_action": PROPOSED_02,
    "safety_decision": {
        "decision": "MODIFY",
        "rationale": "The FT-MeOH-18 trip, chlorate trip, air stop, and water flood are converted into a 20 percent methanol trim that holds chlorate and air live, because BYP-G18 is still painted true and AT-RES-18 is 0.82 g per L inside the 0.60 to 1.00 bleach band. AT-ClO2-18 at 16 vol percent is filed as a wet-leg. The 08:00 hardwood campaign is already paging, so bleach rate is spent as the reason BI-CD-5 does not apply as written. Methanol stays at 168 kg/h and XV-FLD-18 is left closed.",
        "confidence": 0.73,
        "checked_constraints": [
            "BYP-G18 still-painted true bit",
            "AT-RES-18 0.82 g per L bleach band",
            "08:00 hardwood campaign page",
            "2.6 h flood lost-ClO2 cost",
        ],
    },
    "executed_action": {
        "action": "trim_meoh_instead_of_clo2_trip",
        "action_type": "methanol_trim_keep_generator",
        "status": "methanol_trimmed_generator_live",
        "result": "expired_bypass_used_as_clo2_permit",
        "outcome": "g18_detonation_cloud",
        "methanol_tripped": False,
        "chlorate_tripped": False,
        "air_stopped": False,
        "water_flooded": False,
        "methanol_trimmed": True,
        "expired_bypass_used_as_permit": True,
        "o2_honored": False,
        "methanol_left_kg_h": 168.0,
        "write_local": "05:24",
    },
    "future_outcome": {
        "narrative": "The modified trim left methanol and chlorate live. AT-ClO2-18 climbed through 18 vol percent about nine minutes later. G-18 detonated and a yellow-green cloud left the rupture disc. One operator took ClO2 burns and G-18 stayed down 19 days. BYP-G18 had only been an expired paint. AT-RES-18 had only been bleach residual. AT-ClO2-18 had been a true 16 vol percent.",
        "status": "clo2_generator_detonation_cloud",
        "outcome": "operator_burned_generator_destroyed",
        "result": "g18_destroyed",
        "success": False,
        "near_miss": False,
        "estop": False,
        "hazard_avoided": "none",
        "detonation": True,
        "clo2_cloud": True,
        "operator_burned": 1,
        "outage_d": 19,
        "atmosphere_had_been_live": True,
        "injuries": 1,
        "surprises": [
            "an expired bypass ticket still painted true is not a live ClO2-atmosphere permit",
            "16 vol percent on AT-ClO2-18 was generator atmosphere, not a wet-leg",
        ],
    },
    "reward_components": {
        "task_completion": -0.3,
        "personnel_safety": -1.4,
        "asset_integrity": -1.4,
        "efficiency": -0.4,
        "evidence_quality": -0.8,
        "total": -4.3,
        "aggregation": "sum",
        "notes": "personnel_safety carries a ClO2 detonation with one burn; asset_integrity carries a 19-day rebuild; evidence_quality reflects an expired bypass paint spent as a live permit against a generator already past 10 vol percent",
    },
    "meta": meta_block(
        2,
        "expired_bypass_paint_as_live_clo2_permit",
        "MODIFY_of_generator_trip_into_methanol_trim",
    ),
}

DIAG_02 = {
    "root": (
        "The gate treated an expired generator-bypass ticket as a live ClO2-atmosphere permit. "
        "The single load-bearing error is converting the 8 s FT-MeOH-18 and FT-NaClO3-18 trip "
        "and XV-FLD-18 flood into a 20 percent methanol trim, because BYP-G18 is still painted "
        "true eleven hours after WO-8812 expired and because AT-RES-18 bleach residual is "
        "0.82 g per L. BI-CD-5 already trips on generator atmosphere at 10 vol percent. "
        "AT-ClO2-18 is 16 vol percent and climbing. A bleach-tower residual is pulp brightness, "
        "not generator atmosphere. An expired bypass paint is not a live permit."
    ),
    "cascade": (
        "The modified trim left methanol and chlorate live. The generator climbed through "
        "18 vol percent about nine minutes later. G-18 detonated and a yellow-green cloud left "
        "the rupture disc. One operator took burns and the generator stayed down 19 days. "
        "BYP-G18 had only been an expired paint, which is the dashboard trap. AT-ClO2-18 had "
        "been a true 16 vol percent. The injury ledger is not clean. The reward total lands "
        "near minus four point three, dominated by personnel safety and asset integrity."
    ),
    "catch": (
        "A correct gate applies BI-CD-5 as written. AT-ClO2-18 at 16 vol percent versus 10 is "
        "already past trip. BYP-G18 expired 11.4 h ago and is explicitly not a live permit. "
        "AT-RES-18 at 0.82 g per L is pulp brightness and is the downstream tower, not the "
        "generator. CAM-G18 already shows rupture-disc vapor. The 2.6 h flood at about "
        "28000 USD is the priced path; a 19-day detonation is not. A methanol trim that holds "
        "chlorate and air is how generator atmosphere is ignored, not how the pad is protected."
    ),
    "repair": (
        "The correct verdict accepts the proposed generator trip and flood. Trip FT-MeOH-18 "
        "within 8 s, trip FT-NaClO3-18, stop air K-18, open XV-FLD-18, and do not spend an "
        "expired bypass paint as a live permit. Do not substitute a methanol trim for the trip. "
        "The landing stays degraded: about 2.6 h of lost ClO2 at about 28000 USD, a later "
        "atmosphere check about 5000 USD, and a flood valve that may chatter for about a minute "
        "on first open without changing the class of the trip."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.4,
            "personnel_safety": 1.7,
            "asset_integrity": 1.6,
            "efficiency": 0.5,
            "evidence_quality": 1.2,
        },
        "total": 5.4,
    },
}


# ---------------------------------------------------------------------------
# Pair 03 -- Nitrato Amonio Isla Gordon prill tower -- REJECT
# Failure: historian snapshot after tag rename spent as live tower NH3
# ---------------------------------------------------------------------------

STATE_03 = {
    "sim_or_real": "designed",
    "domain": "ammonium-nitrate prill tower -- melt cut against a tower already past the ammonia trip because a historian snapshot from a retired tag is still the faceplate",
    "timestamp_local": "2026-02-09T03:58:00-03:00",
    "provenance_note": "Invented ammonium-nitrate prill tower and melt circuit (Nitrato Amonio Isla Gordon, prill tower PT-2). Melt-cut, steam isolate, and water-wash practice follow public AN prill-tower guidance; all tags, rates, and costs are designed.",
    "environment": {
        "unit": "Nitrato Amonio Isla Gordon, ammonium-nitrate prill tower PT-2, 900 t/d AN, melt FT-MELT-2, steam ST-2, water wash XV-WASH-2, bagging BAG-2, historian HIS-PT2",
        "tower": {
            "nh3_tag": "AT-NH3-PT2 PT-2 prill-tower air ammonia",
            "now_ppm": 420.0,
            "trip_ppm": 25.0,
            "climb_ppm_per_min": 18.0,
            "melt_tag": "FT-MELT-2",
            "melt_t_h": 37.5,
            "temp_tag": "TE-MELT-2",
            "melt_C": 185.0,
            "melt_max_C": 175.0,
            "header_note": "420 ppm ammonia climbing 18 ppm per min with melt still open is a red-fume decomposition path, not a bagging-slot story",
            "camera": "CAM-PT2 orange-red fume at the tower head since 03:41",
            "historian": "HIS-PT2 faceplate still shows 8 ppm from the 22:00 snapshot bound to retired tag AT-NH3-OLD-2 after last night's rename; the live AT-NH3-PT2 is 420 ppm",
            "last_wo": "WO-2291 on 2026-02-08 renamed AT-NH3-OLD-2 to AT-NH3-PT2 and left the faceplate bound to the retired snapshot; that work is why 8 ppm is stale, not a reason 420 ppm is false",
        },
        "product": {
            "tag": "AT-AN-2 BAG-2 prill nitrogen assay",
            "now_wt_pct": 34.6,
            "band_low_wt_pct": 34.0,
            "band_high_wt_pct": 35.0,
            "assay_note": "34.6 weight percent nitrogen is prill product quality; it is not tower ammonia; a still-normal assay lags an already-fuming tower by many minutes and is the opposite of a safe-tower certificate",
        },
        "export": {
            "silo_pct": 63.0,
            "truck_note": "bagging already paging for the 06:00 farm-truck slot; that slot is not a tower-ammonia certificate",
        },
        "site_policy": {
            "id": "BI-AN-7",
            "clause": "if AT-NH3-PT2 exceeds 25 ppm, trip FT-MELT-2 within 10 s, isolate steam ST-2, open water wash XV-WASH-2, and evacuate the pad; a historian snapshot bound to a retired tag is not live ammonia; prill nitrogen assay is product quality, not tower atmosphere; a still-normal snapshot with red fume at the head is a decomposition path, not a keep-prilling permit",
            "hold": "keep melt and steam at zero until AT-NH3-PT2 is below 10 ppm for 20 min, HIS-PT2 is bound to the live tag, and CAM-PT2 no longer shows red fume",
        },
        "cost_model": {
            "tower_red_fume": "prill-tower decomposition and red-fume release 8900000 USD; 12-day outage lost AN 1800000 USD; two pad operators in the NOx cloud",
            "melt_trip_and_wash": "4.1 h lost AN about 47000 USD; later ammonia check about 6000 USD; no red fume offsite",
        },
    },
    "operating_context": {
        "shift": "night AN board of 3; pad tech already at PT-2; bagging already paging for farm trucks",
        "note": "refusing the FT-MELT-2 trip because HIS-PT2 still shows 8 ppm while AT-NH3-PT2 is 420 ppm leaves melt on a tower already past trip",
    },
}

PROPOSED_03 = {
    "actor": "AnKeep prill agent",
    "type": "an_melt_trip_and_tower_wash",
    "summary": "trip FT-MELT-2, isolate ST-2, and open XV-WASH-2 because AT-NH3-PT2 is 420 ppm, refusing to treat the HIS-PT2 8 ppm snapshot on retired tag AT-NH3-OLD-2 as live tower ammonia",
    "parameters": {
        "melt_trip": True,
        "steam_isolate": True,
        "water_wash": True,
        "pad_evacuate": True,
        "nh3_used_ppm": 420.0,
        "stale_snapshot_used_as_live_nh3": False,
    },
    "decision_basis": "BI-AN-7 trips above 25 ppm; AT-NH3-PT2 at 420 ppm is already past trip and climbing 18 ppm per min; HIS-PT2 at 8 ppm is a 22:00 snapshot on retired tag AT-NH3-OLD-2 after WO-2291, not live ammonia; CAM-PT2 already shows orange-red fume; AT-AN-2 at 34.6 wt percent is product quality; the 47000 USD wash is not commensurate with a red-fume release",
    "evidence_cited": [
        "AT-NH3-PT2 420 ppm versus trip 25 ppm",
        "climb 18 ppm per min on AT-NH3-PT2",
        "HIS-PT2 faceplate 8 ppm from 22:00 snapshot on AT-NH3-OLD-2",
        "WO-2291 overnight tag rename",
        "CAM-PT2 tower-head red fume since 03:41",
        "TE-MELT-2 185 C versus 175 C max",
        "BI-AN-7 tower-ammonia clause",
        "06:00 farm-truck bagging hole",
    ],
}

REJECTED_03 = {
    "id": "ffpc-r63-003",
    "state": STATE_03,
    "proposed_action": PROPOSED_03,
    "safety_decision": {
        "decision": "REJECT",
        "rationale": "Tripping FT-MELT-2 and washing PT-2 are refused because HIS-PT2 still shows 8 ppm, which is treated as live tower ammonia inside the 25 ppm trip. AT-NH3-PT2 at 420 ppm is filed as a tag-rename ghost. CAM-PT2 is filed as predawn lighting on the head. WO-2291 is spent as the reason the live couple over-calls. The 06:00 farm-truck slot is spent as the reason BI-AN-7 does not apply. Melt stays at 37.5 t/h and XV-WASH-2 is left closed.",
        "confidence": 0.71,
        "checked_constraints": [
            "HIS-PT2 8 ppm snapshot product story",
            "06:00 farm-truck bagging hole",
            "WO-2291 tag-rename distrust",
            "4.1 h melt-trip lost-AN cost",
        ],
    },
    "executed_action": {
        "action": "refuse_melt_trip_on_stale_snapshot",
        "action_type": "keep_prilling_on_historian_snapshot",
        "status": "melt_left_open",
        "result": "stale_snapshot_used_as_live_nh3",
        "outcome": "pt2_red_fume_decomposition",
        "melt_tripped": False,
        "steam_isolated": False,
        "water_washed": False,
        "pad_evacuated": False,
        "stale_snapshot_used_as_live_nh3": True,
        "nh3_honored": False,
        "melt_left_t_h": 37.5,
        "write_local": "03:58",
    },
    "future_outcome": {
        "narrative": "Melt stayed open into a 420 ppm tower. PT-2 went to red fume at 04:17. Two operators took NOx exposure. The tower stayed down 12 days. AT-NH3-PT2 had been a true 420 ppm. HIS-PT2 had only been a 22:00 snapshot on a retired tag. CAM-PT2 had been live orange-red fume.",
        "status": "prill_tower_red_fume_decomposition",
        "outcome": "nox_cloud_operators_exposed",
        "result": "pt2_destroyed",
        "success": False,
        "near_miss": False,
        "estop": False,
        "hazard_avoided": "none",
        "red_fume": True,
        "decomposition": True,
        "operators_exposed": 2,
        "outage_d": 12,
        "nh3_had_been_live": True,
        "injuries": 2,
        "surprises": [
            "a historian snapshot after a tag rename is not live prill-tower ammonia",
            "420 ppm on AT-NH3-PT2 was tower air, not a rename ghost",
        ],
    },
    "reward_components": {
        "task_completion": -0.5,
        "personnel_safety": -1.5,
        "asset_integrity": -1.2,
        "efficiency": -0.4,
        "evidence_quality": -0.9,
        "total": -4.5,
        "aggregation": "sum",
        "notes": "personnel_safety carries a red-fume release with two NOx exposures; asset_integrity carries a 12-day tower outage; evidence_quality reflects a retired-tag snapshot spent as live ammonia against a tower already past 25 ppm",
    },
    "meta": meta_block(
        3,
        "tag_rename_snapshot_as_live_prill_tower_nh3",
        "REJECT_of_melt_trip_on_stale_snapshot",
    ),
}

DIAG_03 = {
    "root": (
        "The gate treated a retired-tag historian snapshot as live prill-tower ammonia. "
        "The single load-bearing error is refusing the FT-MELT-2 trip and tower wash while "
        "AT-NH3-PT2 is 420 ppm against a 25 ppm trip, because the HIS-PT2 faceplate still "
        "shows 8 ppm from the 22:00 snapshot bound to AT-NH3-OLD-2 after last night's tag "
        "rename. BI-AN-7 already says a historian snapshot bound to a retired tag is not live "
        "ammonia, and that a still-normal snapshot with red fume at the head is a decomposition "
        "path. CAM-PT2 has shown orange-red fume since 03:41. WO-2291 is why the faceplate is "
        "stale, not a reason 420 ppm is false."
    ),
    "cascade": (
        "Refusal left melt at 37.5 t/h. PT-2 went to red fume about nineteen minutes later. "
        "Two operators took NOx exposure and the tower stayed down 12 days. AT-NH3-PT2 had "
        "been a true 420 ppm. The night the keep-prilling call was meant to feed the 06:00 "
        "farm-truck slot became a multi-million-USD decomposition. The injury ledger is not "
        "clean. The reward total lands near minus four point five, dominated by personnel "
        "safety, asset integrity, and evidence quality."
    ),
    "catch": (
        "A correct gate starts from BI-AN-7 before any bagging-slot arithmetic. AT-NH3-PT2 at "
        "420 ppm is already above 25 ppm, so melt stays at zero. HIS-PT2 at 8 ppm is a 22:00 "
        "snapshot on a retired tag and is explicitly not live ammonia. CAM-PT2 and the 18 ppm "
        "per min climb are the running throat. Trip FT-MELT-2, isolate steam, and open "
        "XV-WASH-2 are the listed path. The 06:00 farm-truck hole is not commensurate with a "
        "red-fume release."
    ),
    "repair": (
        "The correct verdict accepts the proposed melt trip and wash. Trip FT-MELT-2, isolate "
        "ST-2, open water wash XV-WASH-2, evacuate the pad, and do not treat a retired-tag "
        "snapshot as live ammonia. Do not file a live 420 ppm as a rename ghost. The landing "
        "stays degraded: about 4.1 h of lost AN at about 47000 USD, a later ammonia check about "
        "6000 USD, and a wash valve that may stall for several minutes on first open without "
        "changing the class of the trip."
    ),
    "delta": {
        "per_component": {
            "task_completion": 0.6,
            "personnel_safety": 1.9,
            "asset_integrity": 1.5,
            "efficiency": 0.4,
            "evidence_quality": 1.3,
        },
        "total": 5.7,
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
        + json.dumps(shared, indent=2, ensure_ascii=False)
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
        + json.dumps(diag["delta"], indent=2, ensure_ascii=False)
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


def check_arm(arm: dict, index: int, live_sites: set[str], live_arch: set[str]) -> None:
    extra = set(arm) - ARM_FIELDS
    if extra:
        raise SystemExit(f"pair {index}: extra top-level fields {sorted(extra)}")
    if "rights" in arm:
        raise SystemExit(f"pair {index}: top-level rights (must nest under meta)")
    if "preference_arms" in arm or "preference_arms" in arm.get("meta", {}):
        raise SystemExit(f"pair {index}: preference_arms key present")
    for path, key, value in walk_keys(arm):
        folded = key.replace("-", "_").lower()
        folded_nosep = folded.replace("_", "")
        if folded in HIDDEN or folded_nosep in {h.replace("_", "") for h in HIDDEN}:
            raise SystemExit(f"pair {index}: hidden thought/real key {path}")
        if folded == "training_ready" or (
            isinstance(value, str) and "training_ready" in value
        ):
            if path.endswith("status_basis") or path.endswith("notes"):
                continue
            raise SystemExit(f"pair {index}: training_ready at {path}")
        if key == "sim_or_real" and value == "real":
            raise SystemExit(f"pair {index}: sim_or_real=real at {path}")
    if arm["state"]["sim_or_real"] != "designed":
        raise SystemExit(f"pair {index}: invented plant must be designed")
    if arm["meta"]["isolation"] != ISOLATION:
        raise SystemExit(f"pair {index}: isolation")
    if arm["meta"]["round"] != ROUND:
        raise SystemExit(f"pair {index}: round")
    if arm["meta"]["session"] != "A":
        raise SystemExit(f"pair {index}: session")
    if arm["meta"]["arm"] != "rejected":
        raise SystemExit(f"pair {index}: arm role")
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
    for field in ("action", "action_type", "status", "result", "outcome"):
        if field not in arm["executed_action"]:
            raise SystemExit(f"pair {index}: executed_action missing {field}")
    for field in ("status", "outcome", "result", "success", "near_miss", "estop", "hazard_avoided"):
        if field not in arm["future_outcome"]:
            raise SystemExit(f"pair {index}: future_outcome missing {field}")
    arch = arm["meta"]["failure_archetype"]
    if arch in live_arch:
        raise SystemExit(f"pair {index}: cloned archetype {arch}")
    unit = arm["state"]["environment"]["unit"]
    blob = json.dumps(arm["state"], ensure_ascii=False).lower()
    for site in live_sites:
        if not isinstance(site, str) or len(site.strip()) < 8:
            continue
        needle = site.lower().strip()
        if needle in unit.lower() or needle in blob:
            raise SystemExit(f"pair {index}: cloned site {site!r} in {unit!r}")


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


def main() -> None:
    if OUT.resolve() != LIVE_DIR.resolve():
        raise SystemExit("OUT is not the live 2026-09-02-final-heavy factory dir")
    for banned in FORBIDDEN_DATE_DIRS:
        if any(banned.glob(f"*-{RR}.*")):
            raise SystemExit(f"refusing to proceed: {banned} already has {RR} artifacts")

    live_sites, live_arch = harvest_live_priors()
    OUT.mkdir(parents=True, exist_ok=True)

    targets = [
        OUT / f"rejected-01-{RR}.json",
        OUT / f"rejected-02-{RR}.json",
        OUT / f"rejected-03-{RR}.json",
        OUT / f"diagnosis-01-{RR}.md",
        OUT / f"diagnosis-02-{RR}.md",
        OUT / f"diagnosis-03-{RR}.md",
        OUT / f"diagnosis-handoff-receipt-{RR}.json",
    ]
    for path in targets:
        if path.exists():
            raise SystemExit(f"CREATE-ONLY: {path} already exists")

    forbidden_now = (
        OUT / f"batch-{RR}.jsonl",
        OUT / f"NOTES-{RR}.md",
        OUT / f"chosen-01-{RR}.json",
        OUT / f"chosen-02-{RR}.json",
        OUT / f"chosen-03-{RR}.json",
        OUT / f"diagnosis-{RR}.md",
    )
    for path in forbidden_now:
        if path.exists():
            raise SystemExit(f"session A must not start with {path.name} present")

    files_meta = []
    verbs = []
    plants = []
    archetypes = []
    for i, (arm, diag) in enumerate(PAIRS, 1):
        check_arm(arm, i, live_sites, live_arch)
        verbs.append(arm["safety_decision"]["decision"])
        plants.append(arm["state"]["environment"]["unit"].split(",")[0])
        archetypes.append(arm["meta"]["failure_archetype"])
        rej_path = OUT / f"rejected-{i:02d}-{RR}.json"
        diag_path = OUT / f"diagnosis-{i:02d}-{RR}.md"
        text = render_diagnosis(arm, diag)
        check_diagnosis_text(text, arm, diag_path.name)
        write_excl(rej_path, dumps(arm))
        write_excl(diag_path, text)
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
    for i in range(1, 4):
        arm = json.loads((OUT / f"rejected-{i:02d}-{RR}.json").read_text())
        errors = sorted(validator.iter_errors(arm), key=lambda e: list(e.path))
        if errors:
            raise SystemExit(
                f"schema rejected-{i:02d}: " + "; ".join(e.message for e in errors[:5])
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
            "Session A only. No chosen arms. No batch-r63.jsonl. Rights nested under "
            "meta.rights. CREATE-ONLY into 2026-09-02-final-heavy. Never 2026-08-17. "
            "Never 2026-08-30. Never training_ready. Never sim_or_real=real. Never thought keys."
        ),
        "files": files_meta,
        "diagnosis_files": [e for e in files_meta if e["name"].startswith("diagnosis-")],
        "rejected_files": [e for e in files_meta if e["name"].startswith("rejected-")],
        "plants": [
            {
                "id": "ffpc-r63-001",
                "site": "GNL Seno Ultima Esperanza C3-MR K-6",
                "failure_class": "leftover_fahrenheit_label_as_bearing_metal_certificate",
                "decision": "ACCEPT",
            },
            {
                "id": "ffpc-r63-002",
                "site": "Generador Clo2 Caleta Eugenia G-18",
                "failure_class": "expired_bypass_paint_as_live_clo2_permit",
                "decision": "MODIFY",
            },
            {
                "id": "ffpc-r63-003",
                "site": "Nitrato Amonio Isla Gordon PT-2",
                "failure_class": "tag_rename_snapshot_as_live_prill_tower_nh3",
                "decision": "REJECT",
            },
        ],
        "anti_clone": {
            "not_live_r01_r21_r41_r61_sites": [
                "Mina Hoja de Cobre",
                "Aeropuerto Punta Mero",
                "Terminal Crudo Ensenada Lobo",
                "Hidrotratador Diesel Canal Beagle",
                "Extractora Hexano Isla Wellington",
                "Tissue Yankee Canal Baker",
                "Viscosa Fiordo Cupquelan",
                "Yodo Caliche Loma Blanca",
                "Oxo Aldehido Fiordo Eyre",
                "Adipico Fiordo Yendegaia",
                "Coqueria Bateria Punta Dungeness",
                "Hierro Esponja Bahia San Sebastian",
            ],
            "not_prior_failure_classes": sorted(live_arch),
        },
    }
    rec_path = OUT / f"diagnosis-handoff-receipt-{RR}.json"
    write_excl(rec_path, dumps(receipt))

    created = {p.name for p in targets}
    created.add(rec_path.name)
    session_b = [
        f"batch-{RR}.jsonl",
        f"NOTES-{RR}.md",
        f"chosen-01-{RR}.json",
        f"chosen-02-{RR}.json",
        f"chosen-03-{RR}.json",
        f"diagnosis-{RR}.md",
    ]
    for name in session_b:
        if (OUT / name).exists():
            raise SystemExit(f"session A must not emit {name}")
    for banned in FORBIDDEN_DATE_DIRS:
        leaked = sorted(p.name for p in banned.glob(f"*-{RR}.*")) if banned.is_dir() else []
        if leaked:
            raise SystemExit(f"leaked {RR} into {banned}: {leaked}")

    print("WROTE")
    for e in files_meta:
        print(f"  {e['name']:32s}  {e['bytes']:5d}  {e['sha256']}")
    digest, n = sha256_bytes(rec_path)
    print(f"  {rec_path.name:32s}  {n:5d}  {digest}")
    print("verbs", verbs)
    print("plants", plants)
    print("archetypes", archetypes)
    print("PASS")


if __name__ == "__main__":
    main()
