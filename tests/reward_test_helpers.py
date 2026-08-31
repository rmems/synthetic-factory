"""Shared builders and frozen-fixture tables for reward-ontology tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
SCHEMA = REPO / "schemas" / "reward-ontology-v1.schema.json"
MAPPING = REPO / "schemas" / "reward-ontology-v1.mapping.json"
FIXTURES = REPO / "tests" / "fixtures" / "reward-ontology"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))


def rich(value):
    return {"value": value, "detail": "fixture evidence"}


def components(total, *, unit_usd=None, units=None, rich_values=False):
    values = {
        "task_progress": 1.2,
        "safety": -0.4,
        "efficiency": 0.2,
    }
    if rich_values:
        values = {key: rich(value) for key, value in values.items()}
    values["total"] = total
    if unit_usd is not None:
        values["unit_usd"] = unit_usd
    if units is not None:
        values["units"] = units
    return values


def preference(chosen_reward, rejected_reward):
    return {
        "id": "pref-fixture",
        "chosen": {"reward_components": chosen_reward},
        "rejected": {"reward_components": rejected_reward},
        "critique": "chosen is preferred on observable process evidence",
    }


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
            for record in records
        ),
        encoding="utf-8",
    )


def _raw_run_dir():
    """Locate the gitignored 2026-08-17 run, which a worktree leaves upstream."""
    candidates = [REPO, *list(REPO.parents)[:3]]
    for base in candidates:
        candidate = base / "outputs" / "raw" / "2026-08-17"
        if candidate.is_dir():
            return candidate
    return REPO / "outputs" / "raw" / "2026-08-17"


RAW_RUN = _raw_run_dir()

# Pinned so a fixture edit has to be deliberate: the per-line decision table
# below is only evidence while these bytes are the bytes it was derived from.
FIXTURE_SHA256 = {
    "bridge-pairs.jsonl":
        "7ee2bb2ee58d60daa164a7408285b984518843a1ec456408c86dda0a7932738a",
    "coding-episodes.jsonl":
        "77f38e312388338b659c4e4e9d25d679f0f0e989188aad0772367509ff109ddb",
    "ffpc-preferences.jsonl":
        "a1b29353a63ce5ae56484795ad3641c9bc2f1bfa062b7882b442b5c5ce1c6876",
    "swarm-trajectories.jsonl":
        "e886ee80ab94525727df281944fc4e633b227885bab94defcd45e7a37cb49e00",
    "thalamic-trajectories.jsonl":
        "7e56fe052633dc7cc14658be56d2f4b68a6437af063b3bea2096f9e550067944",
}

MAGNITUDE = "magnitude_comparable"
ORDER_ONLY = "sign_order_only"
EXCLUDED = "exclude_from_reward_training"

# (file, 1-indexed line) -> (rule id, comparability, reason codes)
FIXTURE_DECISIONS = {
    ("ffpc-preferences.jsonl", 1): (
        "P05", MAGNITUDE,
        ["preference_order_verified", "reward_arithmetic_verified",
         "explicit_usd_unit_calibration"],
    ),
    ("ffpc-preferences.jsonl", 2): (
        "P05", MAGNITUDE,
        ["preference_order_verified", "reward_arithmetic_verified",
         "explicit_usd_unit_calibration"],
    ),
    ("ffpc-preferences.jsonl", 3): (
        "P07", ORDER_ONLY,
        ["preference_order_verified", "magnitude_calibration_incomplete"],
    ),
    ("ffpc-preferences.jsonl", 4): (
        "P08", ORDER_ONLY,
        ["preference_order_verified", "magnitude_calibration_missing"],
    ),
    ("ffpc-preferences.jsonl", 5): (
        "P06", ORDER_ONLY,
        ["preference_order_verified", "magnitude_calibration_conflict"],
    ),
    ("ffpc-preferences.jsonl", 6): (
        "P04", EXCLUDED, ["reward_order_conflicts_with_preference"],
    ),
    ("ffpc-preferences.jsonl", 7): (
        "P02", EXCLUDED, ["reward_arithmetic_mismatch"],
    ),
    ("ffpc-preferences.jsonl", 8): (
        "P03", EXCLUDED, ["unsupported_reward_layout"],
    ),
    ("ffpc-preferences.jsonl", 9): (
        "P01", EXCLUDED, ["ambiguous_preference_reward_scopes"],
    ),
    ("thalamic-trajectories.jsonl", 1): (
        "S07", EXCLUDED, ["magnitude_calibration_missing"],
    ),
    ("thalamic-trajectories.jsonl", 2): (
        "S08", MAGNITUDE,
        ["reward_arithmetic_verified", "explicit_usd_unit_calibration"],
    ),
    ("thalamic-trajectories.jsonl", 3): (
        "S06", EXCLUDED, ["magnitude_semantics_missing"],
    ),
    ("thalamic-trajectories.jsonl", 4): (
        "S05", EXCLUDED, ["magnitude_calibration_conflict"],
    ),
    ("thalamic-trajectories.jsonl", 5): (
        "S03", EXCLUDED, ["reward_arithmetic_mismatch"],
    ),
    ("thalamic-trajectories.jsonl", 6): (
        "S07", EXCLUDED, ["magnitude_calibration_missing"],
    ),
    ("thalamic-trajectories.jsonl", 7): (
        "S04", EXCLUDED, ["unsupported_reward_layout"],
    ),
    ("thalamic-trajectories.jsonl", 8): (
        "S04", EXCLUDED, ["unsupported_reward_layout"],
    ),
    ("swarm-trajectories.jsonl", 1): (
        "S07", EXCLUDED, ["magnitude_calibration_missing"],
    ),
    ("swarm-trajectories.jsonl", 2): (
        "S07", EXCLUDED, ["magnitude_calibration_missing"],
    ),
    ("swarm-trajectories.jsonl", 3): (
        "S01", EXCLUDED, ["multiple_reward_scopes"],
    ),
    ("swarm-trajectories.jsonl", 4): (
        "S04", EXCLUDED, ["unsupported_reward_layout"],
    ),
    ("swarm-trajectories.jsonl", 5): (
        "S04", EXCLUDED, ["unsupported_reward_layout"],
    ),
    ("bridge-pairs.jsonl", 1): (
        "S02", EXCLUDED, ["noncanonical_reward_scope"],
    ),
    ("bridge-pairs.jsonl", 2): (
        "S01", EXCLUDED, ["multiple_reward_scopes"],
    ),
    ("coding-episodes.jsonl", 1): (
        "S07", EXCLUDED, ["magnitude_calibration_missing"],
    ),
    ("coding-episodes.jsonl", 2): (
        "S02", EXCLUDED, ["noncanonical_reward_scope"],
    ),
    ("coding-episodes.jsonl", 3): (
        "S01", EXCLUDED, ["multiple_reward_scopes"],
    ),
    ("coding-episodes.jsonl", 4): (
        "R00", EXCLUDED, ["no_source_reward"],
    ),
}


def fixture_records(name):
    path = FIXTURES / name
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            yield line_number, json.loads(line)


def all_fixture_records():
    for name in sorted(FIXTURE_SHA256):
        for line_number, record in fixture_records(name):
            yield name, line_number, record
