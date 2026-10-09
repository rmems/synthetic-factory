#!/usr/bin/env python3
"""Fresh replay: rebuild the environment and re-execute a record's own actions.

Replay is the oracle every gate calls. It needs only the pinned catalog and
the record: the pack by id and digest, the task, the seed, and the recorded
action sequence. The solver-owned facts (the calls, each decision basis, the
variant, whether it gave up, how many faults it recovered, its version and
run id) are read once; every other field is re-derived from the replayed
environment through the same builders ``records`` uses and compared, so a
record cannot relabel itself, forge its evidence, or edit its trainable
projection without a reported mismatch.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import env as environment
from . import records
from . import vocabulary as cv
from ._contract import bind_import_twin, load_strict_json, sha256_bytes
from .policies import scripted

__all__ = ["ReplayResult", "load_records", "replay_record", "replay_run"]

CANDIDATES_FILENAME = "candidates.jsonl"
RUN_FILENAME = "RUN.json"
_META_DERIVED = (
    "factory",
    "generator",
    "generator_version",
    "generator_kind",
    "kind",
    "family",
    "surface",
    "variant",
    "seed",
    "designed",
)
_PINNED_MESSAGES = {
    "oracle.result_hash": "oracle.result_hash differs from the replay digest",
    "payload.final_state_digest": "final state digest differs",
    "payload.predicate_results": "predicate verdicts differ",
    "training_view.reward.success": "reward.success differs from the replayed verdict",
}


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


@dataclass(frozen=True)
class _SolverFacts:
    """What only the solver knows; replay copies these and derives everything else."""

    variant: str
    policy: str
    run_id: str
    draw: int
    gave_up: bool
    faults_recovered: int
    cost_steps: int

    def context(self, catalog_sha256: str) -> records.RunContext:
        return records.RunContext(catalog_sha256, self.run_id, self.policy)


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


def _require_typed(record: Mapping[str, Any], kind: type, *path: str) -> Any:
    value = _require(record, *path)
    cv.refuse_when(
        not isinstance(value, kind) or (kind is int and isinstance(value, bool)),
        cv.FINDING_RECORD_MALFORMED,
        f"{'.'.join(path)} must be {kind.__name__}",
    )
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
        f"record was generated from pack digest {record['environment']['pack_sha256']}, "
        f"catalog has {pack.pack_sha256}",
    )
    task = pack.task(_require(record, "environment", "task_id"))
    return environment.Environment(pack, task, _require(record, "environment", "seed"))


def _solver_facts(record: Mapping[str, Any], task: Any, cost_steps: int) -> _SolverFacts:
    variant = _require_typed(record, str, "training_view", "meta", "variant")
    cv.refuse_when(
        variant != cv.VARIANT_GOLD and variant not in task.perturbations,
        cv.FINDING_RECORD_MALFORMED,
        f"variant {variant!r} is neither gold nor a perturbation of {task.task_id}",
    )
    identifier = _require_typed(record, str, "id")
    tail = identifier.rsplit("-", 1)[-1]
    cv.refuse_when(
        not tail.isdigit(), cv.FINDING_RECORD_MALFORMED, "id must end in the draw number"
    )
    evidence = ("payload", "execution_evidence")
    return _SolverFacts(
        variant=variant,
        policy=_require_typed(record, str, "solver", "version"),
        run_id=_require_typed(record, str, "solver", "run_id"),
        draw=int(tail),
        gave_up=_require_typed(record, bool, *evidence, "gave_up"),
        faults_recovered=_require_typed(record, int, *evidence, "faults_recovered"),
        cost_steps=cost_steps,
    )


def _sequences(record: Mapping[str, Any], task: Any) -> tuple[list[Any], list[Any]]:
    actions = _require(record, "payload", "actions")
    steps = _require(record, "training_view", "steps")
    cv.refuse_when(
        not isinstance(actions, list) or not isinstance(steps, list),
        cv.FINDING_RECORD_MALFORMED,
        "actions and steps must be lists",
    )
    cv.refuse_when(
        len(actions) > task.max_steps,
        cv.FINDING_RECORD_MALFORMED,
        f"{len(actions)} actions exceed max_steps {task.max_steps}",
    )
    for index, step in enumerate(steps):
        cv.refuse_when(
            not isinstance(step, Mapping),
            cv.FINDING_RECORD_MALFORMED,
            f"training_view.steps[{index}] must be an object",
        )
    return actions, steps


def _action_mismatches(
    n: int, action: Mapping[str, Any], event: Any, observation: Any
) -> list[str]:
    mismatches = []
    if observation.full_sha256 != action.get("observation_sha256"):
        mismatches.append(f"step {n}: observation digest differs")
    if observation.fault_id != action.get("fault_id"):
        mismatches.append(
            f"step {n}: fault {observation.fault_id!r} differs from recorded "
            f"{action.get('fault_id')!r}"
        )
    if action != event.row():
        mismatches.append(f"step {n}: payload action row differs from the replayed event")
    return mismatches


def _view_step_mismatches(
    n: int, step: Mapping[str, Any], event: Any, observation: Any
) -> list[str]:
    mismatches = []
    if step.get("observation") != observation.text:
        mismatches.append(f"step {n}: training_view observation text differs")
    if step.get("tool_call") != event.row()["tool_call"]:
        mismatches.append(f"step {n}: training_view tool_call differs")
    if step.get("n") != n:
        mismatches.append(f"step {n}: training_view step number differs")
    return mismatches


def _step_mismatches(env: Any, actions: list[Any], steps: list[Any]) -> list[str]:
    mismatches = []
    for index, action in enumerate(actions):
        cv.refuse_when(
            not isinstance(action, Mapping) or not isinstance(action.get("tool_call"), Mapping),
            cv.FINDING_RECORD_MALFORMED,
            f"actions[{index}] must carry a tool_call",
        )
        observation = env.step(action["tool_call"])
        event = env.events[-1]
        mismatches.extend(_action_mismatches(index + 1, action, event, observation))
        if index < len(steps):
            mismatches.extend(_view_step_mismatches(index + 1, steps[index], event, observation))
    if len(steps) != len(actions):
        mismatches.append(
            f"training_view has {len(steps)} steps, payload has {len(actions)} actions"
        )
    return mismatches


def _expected(
    env: Any, facts: _SolverFacts, verdict: Mapping[str, Any], catalog: Any
) -> dict[str, Any]:
    """Every field replay derives, built by the record builders from the replayed environment."""
    task, pack = env.task, env.pack
    run = facts.context(catalog.catalog_sha256)
    success = bool(verdict["success"])
    replay_digest = env.replay_digest()
    identifier = records.record_id(pack.pack_sha256, run.policy, env.seed, facts.draw)
    payload = records.payload(env, facts, verdict, replay_digest)
    del payload["actions"]  # compared step by step above
    meta = records.training_meta(task, facts.variant, env.seed)
    return {
        "schema_version": cv.RECORD_SCHEMA_VERSION,
        "record_kind": cv.RECORD_KIND_BY_SURFACE[task.surface],
        "family": cv.FAMILY,
        "id": identifier,
        "task_author": records.task_author(pack, task, run.run_id),
        "solver": records.solver(task, facts.variant, run, success),
        "oracle": records.oracle(pack, identifier, replay_digest, success),
        "curation": records.curation(facts.variant, success),
        "environment": records.environment(env, run.catalog_sha256),
        "payload": payload,
        "training_view": {
            "id": identifier,
            "goal": task.goal,
            "outcome": records.outcome_text(task.title, success, facts.gave_up),
            "reward": {
                "success": success,
                "cost_steps": facts.cost_steps,
                "faults_recovered": facts.faults_recovered,
            },
            "meta": {key: meta[key] for key in _META_DERIVED},
        },
    }


def _compared_whole(expected: Any, path: str) -> bool:
    """A pinned path is compared as one value, as is anything that is not an object."""
    return path in _PINNED_MESSAGES or not isinstance(expected, Mapping)


def _leaf_mismatch(expected: Any, actual: Any, path: str) -> list[str]:
    if expected == actual:
        return []
    return [_PINNED_MESSAGES.get(path, f"{path} differs from the replayed value")]


def _child_path(path: str, key: str) -> str:
    return f"{path}.{key}" if path else key


def _mapping_mismatches(expected: Mapping[str, Any], actual: Any, path: str) -> list[str]:
    cv.refuse_when(
        not isinstance(actual, Mapping), cv.FINDING_RECORD_MALFORMED, f"{path} must be an object"
    )
    mismatches = []
    for key, value in expected.items():
        child = _child_path(path, key)
        cv.refuse_when(key not in actual, cv.FINDING_RECORD_MALFORMED, f"record lacks {child}")
        mismatches.extend(_diff(value, actual[key], child))
    return mismatches


def _diff(expected: Any, actual: Any, path: str) -> list[str]:
    """Leaf-wise disagreements between a derived block and the record, by dotted path."""
    if _compared_whole(expected, path):
        return _leaf_mismatch(expected, actual, path)
    return _mapping_mismatches(expected, actual, path)


def _scripted_mismatches(record: Mapping[str, Any], env: Any, facts: _SolverFacts) -> list[str]:
    """A record claiming the scripted policy must be the trajectory that policy produces."""
    if _require(record, "solver", "model") != cv.GENERATOR_NAME:
        return []
    if facts.policy != scripted.policy_sha256():
        return ["solver.version is not the loaded scripted policy, so its plan cannot be re-run"]
    fresh = environment.Environment(env.pack, env.task, env.seed)
    trajectory = scripted.run(fresh, facts.variant)
    produced = [
        (step.decision_basis, event.row()["tool_call"])
        for step, event in zip(trajectory.steps, fresh.events, strict=True)
    ]
    recorded = [
        (step.get("decision_basis"), row["tool_call"])
        for row, step in zip(record["payload"]["actions"], record["training_view"]["steps"])
    ]
    mismatches = []
    if produced != recorded:
        mismatches.append(f"the scripted policy replays a different {facts.variant} trajectory")
    if (trajectory.gave_up, trajectory.faults_recovered) != (facts.gave_up, facts.faults_recovered):
        mismatches.append("gave_up or faults_recovered differ from the scripted policy's run")
    return mismatches


def _view_gate_mismatches(view: Mapping[str, Any]) -> list[str]:
    """The episode gate the builder applied, re-applied to the record's own training view."""
    try:
        records.check_training_view(view)
    except cv.ToolWorldRefusal as exc:
        return [f"training_view fails the episode gate: {exc}"]
    return []


def replay_record(record: Mapping[str, Any], catalog: Any) -> ReplayResult:
    """Re-execute one record and report every disagreement."""
    cv.refuse_when(
        not isinstance(record, Mapping), cv.FINDING_INPUT_NOT_AN_OBJECT, "record must be an object"
    )
    env = _bound_environment(record, catalog)
    actions, steps = _sequences(record, env.task)
    facts = _solver_facts(record, env.task, len(steps))
    mismatches = _step_mismatches(env, actions, steps)
    verdict = env.verdict()
    expected = _expected(env, facts, verdict, catalog)
    mismatches.extend(_diff(expected, record, ""))
    mismatches.extend(_view_gate_mismatches(record["training_view"]))
    mismatches.extend(_scripted_mismatches(record, env, facts))
    return ReplayResult(
        str(record.get("id")),
        not mismatches,
        tuple(mismatches),
        env.replay_digest(),
        bool(verdict["success"]),
    )


def _run_summary(run_dir: Path) -> Mapping[str, Any]:
    run_file = run_dir / RUN_FILENAME
    cv.refuse_when(not run_file.is_file(), cv.FINDING_RUN_FILE_MISSING, f"missing {RUN_FILENAME}")
    try:
        summary = load_strict_json(run_file.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise cv.ToolWorldRefusal(
            cv.FINDING_RUN_FILE_INVALID, f"{RUN_FILENAME} is not strict JSON ({exc})"
        ) from exc
    cv.refuse_when(
        not isinstance(summary, Mapping),
        cv.FINDING_RUN_FILE_INVALID,
        f"{RUN_FILENAME} must be an object",
    )
    return summary


def _candidate_lines(run_dir: Path, summary: Mapping[str, Any]) -> list[str]:
    candidates = run_dir / CANDIDATES_FILENAME
    cv.refuse_when(
        not candidates.is_file(), cv.FINDING_RUN_FILE_MISSING, f"missing {CANDIDATES_FILENAME}"
    )
    payload = candidates.read_bytes()
    cv.refuse_when(
        summary.get("candidates_sha256") != sha256_bytes(payload),
        cv.FINDING_RUN_SHA_MISMATCH,
        f"{CANDIDATES_FILENAME} bytes do not match RUN.json candidates_sha256",
    )
    try:
        return payload.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        cv.refuse(cv.FINDING_RECORD_MALFORMED, f"{CANDIDATES_FILENAME} is not UTF-8 ({exc.reason})")


def _parse_record(line: str, number: int) -> Mapping[str, Any]:
    try:
        record = load_strict_json(line)
    except ValueError as exc:
        raise cv.ToolWorldRefusal(
            cv.FINDING_RECORD_MALFORMED, f"line {number} is not strict JSON ({exc})"
        ) from exc
    cv.refuse_when(
        not isinstance(record, Mapping),
        cv.FINDING_RECORD_MALFORMED,
        f"line {number} is not an object",
    )
    return record


def load_records(run_dir: Path) -> list[Mapping[str, Any]]:
    """Every candidate of a run whose bytes RUN.json vouches for; any corruption is a refusal."""
    run_dir = Path(run_dir)
    candidates = run_dir / CANDIDATES_FILENAME
    cv.refuse_when(
        not candidates.is_file(), cv.FINDING_RUN_FILE_MISSING, f"missing {CANDIDATES_FILENAME}"
    )
    lines = _candidate_lines(run_dir, _run_summary(run_dir))
    return [_parse_record(line, number) for number, line in enumerate(lines, 1) if line.strip()]


def _selected(records: list[Mapping[str, Any]], record_id: str | None) -> list[Mapping[str, Any]]:
    if record_id is None:
        return records
    chosen = [record for record in records if record.get("id") == record_id]
    cv.refuse_when(not chosen, cv.FINDING_RECORD_NOT_FOUND, f"record {record_id} is not in the run")
    return chosen


def replay_run(run_dir: Path, catalog: Any, record_id: str | None = None) -> dict[str, Any]:
    """Replay every candidate of a run, or the one named; it passes only when every record agrees.

    The run must have been generated from the loaded catalog: a RUN.json pinned to
    another catalog digest is refused before any record is replayed.
    """
    run_dir = Path(run_dir)
    records = _selected(load_records(run_dir), record_id)
    pinned = _run_summary(run_dir).get("catalog_sha256")
    cv.refuse_when(
        pinned != catalog.catalog_sha256,
        cv.FINDING_RUN_SHA_MISMATCH,
        f"{RUN_FILENAME} was generated from catalog {pinned}, loaded {catalog.catalog_sha256}",
    )
    results = [replay_record(record, catalog).row() for record in records]
    return {
        "run_dir": str(run_dir),
        "record_id": record_id,
        "records": len(results),
        "agreeing": sum(1 for row in results if row["agreement"]),
        "passed": all(row["agreement"] for row in results),
        "results": results,
    }


bind_import_twin(__name__)
