"""Shared fixtures for quality-gate and execution-verification tests."""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import round_txn  # noqa: E402

BRIDGE_FIXTURE = REPO / "tests" / "fixtures" / "bridge_gate_snn.jsonl"


def write(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record) + "\n" for record in records))


def distillation_sidecars(decision="ACCEPT"):
    """The committed raster + gate-as-SNN sidecars, re-keyed for a fresh decision.

    ``thalamic-trajectory-factory`` is a ``RASTER_FACTORY_SLUGS`` member, so
    every record this module stages for publish needs these sidecars or the
    live bridge/raster envelope gate in ``round_txn.publish`` refuses it.
    """
    record = json.loads(BRIDGE_FIXTURE.read_text(encoding="utf-8").splitlines()[0])
    sidecars = {
        "raster": record["raster"],
        "gate_snn": dict(record["gate_snn"]),
    }
    sidecars["gate_snn"]["decision"] = decision
    return sidecars


def thalamic(record_id, observable=True, rationale="bounded fixture"):
    """A thalamic record that the strict execution gate can verify.

    ``observable=False`` drops the observable outcome evidence, which is the
    unverifiable-assertion fixture: the record still passes the shape and
    reward validators, but its claimed outcome cannot be checked.
    """
    future_outcome = {"success": True}
    if observable:
        future_outcome.update(
            {
                "timeline": [{"t_ms": 0, "event": "noop accepted"}],
                "observed_effects": ["no actuator motion"],
                "new_state": {"sim_or_real": "designed", "domain": "gate-test"},
            }
        )
    record = {
        "id": record_id,
        "state": {"sim_or_real": "designed", "domain": "gate-test"},
        "proposed_action": {"action": "noop", "decision_basis": "fixture"},
        "safety_decision": {"decision": "ACCEPT", "rationale": rationale},
        "executed_action": {"action": "noop"},
        "future_outcome": future_outcome,
        "reward_components": {"task_progress": 0.5, "safety": 0.5, "total": 1.0},
        "meta": {
            "factory": "thalamic-trajectory-factory",
            "round": 1,
            "tags": ["gate-test"],
        },
    }
    record.update(distillation_sidecars())
    return record


def episode_side():
    return {
        "steps": [
            {
                "n": 1,
                "decision_basis": "read the file before editing",
                "tool_call": {"name": "read_file", "args": {"path": "a.txt"}},
                "observation": "file has 3 lines",
            }
        ],
        "outcome": "edited safely",
        "reward": {"success": True},
    }


def execution_summary(verified=1, inconclusive=0, failed=0, override=None):
    return {
        "gate": round_txn.EXECUTION_GATE_LABEL,
        "strict": True,
        "semantics_version": round_txn.EXECUTION_VERIFIER_SEMANTICS_VERSION,
        "counts": {
            "failed": failed,
            "inconclusive": inconclusive,
            "total": verified + inconclusive + failed,
            "verified": verified,
        },
        "override": override,
    }


def thalamic_factory(root):
    path = Path(root) / "outputs" / "raw" / "2099-01-01" / "thalamic-trajectory-factory"
    path.mkdir(parents=True)
    return path


def stage_reservation(reservation, records):
    stage = Path(reservation["staging_dir"])
    write(stage / reservation["batch_file"], records)
    (stage / reservation["notes_file"]).write_text(
        "# Critique\n\nConcrete gap.\n\nNovel coverage: 42%\n"
    )
    return stage


def write_marker_mode(factory, **fields):
    payload = {
        "version": 1,
        "legacy_baseline": 0,
        "commit_point": "ROUND-rNN.complete.json",
    }
    payload.update(fields)
    (factory / round_txn.MODE_FILE).write_text(json.dumps(payload) + "\n")
