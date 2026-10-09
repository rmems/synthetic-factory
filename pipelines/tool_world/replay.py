#!/usr/bin/env python3
"""Fresh replay: rebuild the environment and re-execute a record's own actions.

Replay is the oracle every gate calls. It needs only the pinned catalog and
the record: the pack by id and digest, the task, the seed, and the recorded
action sequence. Every observation digest, the bounded observation text in
the training view, the fault ids, the final state digest, the predicate
verdicts, and the replay digest must agree, or the record is a mismatch.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import env as environment
from . import vocabulary as cv
from ._contract import bind_import_twin, load_strict_json, sha256_bytes

__all__ = ["ReplayResult", "replay_record", "replay_run"]

CANDIDATES_FILENAME = "candidates.jsonl"
RUN_FILENAME = "RUN.json"


@dataclass(frozen=True)
class ReplayResult:
    record_id: str
    agreement: bool
    mismatches: tuple[str, ...]
    replay_digest: str
    success: bool

    def row(self) -> dict[str, Any]:
        return {
            "id": self.record_id,
            "agreement": self.agreement,
            "mismatches": list(self.mismatches),
            "replay_digest": self.replay_digest,
            "success": self.success,
        }


def _require(record: Mapping[str, Any], *path: str) -> Any:
    value: Any = record
    for key in path:
        cv.refuse_when(
            not isinstance(value, Mapping) or key not in value,
            cv.FINDING_RECORD_MALFORMED,
            f"record lacks {'.'.join(path)}",
        )
        value = value[key]
    return value


def _bound_environment(record: Mapping[str, Any], catalog: Any) -> Any:
    cv.refuse_when(
        record.get("schema_version") != cv.RECORD_SCHEMA_VERSION,
        cv.FINDING_RECORD_MALFORMED,
        f"schema_version must be {cv.RECORD_SCHEMA_VERSION}",
    )
    pack = catalog.pack(_require(record, "environment", "pack_id"))
    cv.refuse_when(
        pack.pack_sha256 != _require(record, "environment", "pack_sha256"),
        cv.FINDING_PACK_SHA_MISMATCH,
        f"record was generated from pack digest {record['environment']['pack_sha256']}, catalog has {pack.pack_sha256}",
    )
    task = pack.task(_require(record, "environment", "task_id"))
    return environment.Environment(pack, task, _require(record, "environment", "seed"))


def _step_mismatches(env: Any, actions: list[Any], steps: list[Any]) -> list[str]:
    mismatches = []
    for index, action in enumerate(actions):
        cv.refuse_when(
            not isinstance(action, Mapping) or not isinstance(action.get("tool_call"), Mapping),
            cv.FINDING_RECORD_MALFORMED,
            f"actions[{index}] must carry a tool_call",
        )
        observation = env.step(action["tool_call"])
        n = index + 1
        if observation.full_sha256 != action.get("observation_sha256"):
            mismatches.append(f"step {n}: observation digest differs")
        if observation.fault_id != action.get("fault_id"):
            mismatches.append(
                f"step {n}: fault {observation.fault_id!r} differs from recorded {action.get('fault_id')!r}"
            )
        if index < len(steps) and steps[index].get("observation") != observation.text:
            mismatches.append(f"step {n}: training_view observation text differs")
    if len(steps) != len(actions):
        mismatches.append(
            f"training_view has {len(steps)} steps, payload has {len(actions)} actions"
        )
    return mismatches


def replay_record(record: Mapping[str, Any], catalog: Any) -> ReplayResult:
    """Re-execute one record and report every disagreement."""
    cv.refuse_when(
        not isinstance(record, Mapping), cv.FINDING_INPUT_NOT_AN_OBJECT, "record must be an object"
    )
    env = _bound_environment(record, catalog)
    actions = _require(record, "payload", "actions")
    steps = _require(record, "training_view", "steps")
    cv.refuse_when(
        not isinstance(actions, list) or not isinstance(steps, list),
        cv.FINDING_RECORD_MALFORMED,
        "actions and steps must be lists",
    )
    cv.refuse_when(
        len(actions) > env.task.max_steps,
        cv.FINDING_RECORD_MALFORMED,
        f"{len(actions)} actions exceed max_steps {env.task.max_steps}",
    )
    mismatches = _step_mismatches(env, actions, steps)
    verdict = env.verdict()
    recorded = _require(record, "payload", "predicate_results")
    if {"public": verdict["public"], "hidden": verdict["hidden"]} != recorded:
        mismatches.append("predicate verdicts differ")
    if env.snapshot_digest() != _require(record, "payload", "final_state_digest"):
        mismatches.append("final state digest differs")
    replay_digest = env.replay_digest()
    if f"sha256:{replay_digest}" != _require(record, "oracle", "result_hash"):
        mismatches.append("oracle.result_hash differs from the replay digest")
    success_recorded = _require(record, "training_view", "reward").get("success")
    if verdict["success"] != success_recorded:
        mismatches.append("reward.success differs from the replayed verdict")
    return ReplayResult(
        str(record.get("id")),
        not mismatches,
        tuple(mismatches),
        replay_digest,
        bool(verdict["success"]),
    )


def _records(run_dir: Path) -> list[Mapping[str, Any]]:
    candidates = run_dir / CANDIDATES_FILENAME
    cv.refuse_when(
        not candidates.is_file(), cv.FINDING_RUN_FILE_MISSING, f"missing {CANDIDATES_FILENAME}"
    )
    run_file = run_dir / RUN_FILENAME
    cv.refuse_when(not run_file.is_file(), cv.FINDING_RUN_FILE_MISSING, f"missing {RUN_FILENAME}")
    summary = load_strict_json(run_file.read_text(encoding="utf-8"))
    payload = candidates.read_bytes()
    cv.refuse_when(
        not isinstance(summary, Mapping)
        or summary.get("candidates_sha256") != sha256_bytes(payload),
        cv.FINDING_RUN_SHA_MISMATCH,
        f"{CANDIDATES_FILENAME} bytes do not match RUN.json candidates_sha256",
    )
    records = []
    for number, line in enumerate(payload.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        record = load_strict_json(line)
        cv.refuse_when(
            not isinstance(record, Mapping),
            cv.FINDING_RECORD_MALFORMED,
            f"line {number} is not an object",
        )
        records.append(record)
    return records


def replay_run(run_dir: Path, catalog: Any) -> dict[str, Any]:
    """Replay every candidate of a run; the run passes only when every record agrees."""
    results = [replay_record(record, catalog).row() for record in _records(Path(run_dir))]
    return {
        "run_dir": str(run_dir),
        "records": len(results),
        "agreeing": sum(1 for row in results if row["agreement"]),
        "passed": all(row["agreement"] for row in results),
        "results": results,
    }


bind_import_twin(__name__)
