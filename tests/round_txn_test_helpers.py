"""Shared records and staging helpers for round-transaction tests."""

import json
from pathlib import Path

from distillation_test_helpers import distillation_sidecars, load_bridge_fixture

REPO = Path(__file__).resolve().parents[1]


def thalamic(record_id, round_number=1):
    record = {
        "id": record_id,
        "state": {"sim_or_real": "designed", "domain": "transaction-test"},
        "proposed_action": {"action": "noop", "decision_basis": "fixture"},
        "safety_decision": {"decision": "ACCEPT", "rationale": "bounded fixture"},
        "executed_action": {"action": "noop"},
        "future_outcome": {
            "success": True,
            "timeline": [{"t_ms": 0, "event": "noop accepted"}],
            "observed_effects": ["no actuator motion"],
            "new_state": {
                "sim_or_real": "designed",
                "domain": "transaction-test",
            },
        },
        "reward_components": {
            "task_progress": 0.5,
            "safety": 0.5,
            "total": 1.0,
        },
        "meta": {
            "factory": "thalamic-trajectory-factory",
            "round": round_number,
            "tags": ["transaction-test"],
        },
    }
    record.update(distillation_sidecars())
    return record


def bridge(record_id, *, gate_snn=True):
    """Return the committed raster/gate-SNN Bridge fixture with fresh IDs."""

    record = load_bridge_fixture()
    record["id"] = record_id
    trajectory = record["language_view"]["trajectory"]
    trajectory["id"] = f"{record_id}-traj"
    trajectory["state"]["episode_id"] = record_id
    trajectory["meta"]["round"] = 1
    if not gate_snn:
        del record["gate_snn"]
    return record


def write_records(path, records):
    path.write_text("".join(json.dumps(record) + "\n" for record in records))


def raw_factory(root, slug):
    path = Path(root) / "outputs" / "raw" / "2099-01-01" / slug
    path.mkdir(parents=True)
    return path


def stage_round(round_txn, factory, records, *, coverage=100):
    reservation = round_txn.reserve(factory, 1, len(records))
    staging = Path(reservation["staging_dir"])
    write_records(staging / reservation["batch_file"], records)
    (staging / reservation["notes_file"]).write_text(
        f"# Critique\n\nConcrete gap.\n\nNovel coverage: {coverage}%\n"
    )
    return reservation
