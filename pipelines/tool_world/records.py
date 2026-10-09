#!/usr/bin/env python3
"""Assemble one trajectory into a tool-world record.

The record separates who proposed (``solver``), what was proposed and
observed (``payload.actions``), what the environment decided (``oracle``,
``payload.predicate_results``), and the trainable projection
(``training_view``, the repository episode envelope). The training view is
validated by the repository's own episode gate with hidden thought forbidden
and terminal outcome enforced; a record that fails it is refused, not fixed.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from . import vocabulary as cv
from ._contract import (
    bind_import_twin,
    check_episode,
    contains_hidden_reasoning_key,
    sha256_canonical,
)

__all__ = ["build_record", "record_id", "training_view"]


def record_id(pack_sha256: str, policy_sha256: str, seed: int, draw: int) -> str:
    return f"{cv.RECORD_ID_PREFIX}-{pack_sha256[:16]}-{policy_sha256[:16]}-{seed}-{draw:05d}"


def _outcome_text(task: Any, success: bool, trajectory: Any) -> str:
    if success:
        return f"Succeeded: {task.title}"
    if trajectory.gave_up:
        return "Failed: gave up after the first fault instead of recovering"
    return f"Failed: {task.title} was not achieved"


def training_view(
    identifier: str, task: Any, trajectory: Any, success: bool, meta: Mapping[str, Any]
) -> dict[str, Any]:
    steps = [
        {
            "n": step.n,
            "decision_basis": step.decision_basis,
            "tool_call": {"name": step.tool_call["name"], "args": dict(step.tool_call["args"])},
            "observation": step.observation,
        }
        for step in trajectory.steps
    ]
    return {
        "id": identifier,
        "goal": task.goal,
        "steps": steps,
        "outcome": _outcome_text(task, success, trajectory),
        "reward": {
            "success": success,
            "cost_steps": len(steps),
            "faults_recovered": trajectory.faults_recovered,
        },
        "meta": dict(meta),
    }


def _check_training_view(view: Mapping[str, Any]) -> None:
    problems = check_episode(
        view, "training_view", forbid_hidden_thought=True, enforce_terminal_outcome=True
    )
    cv.refuse_when(bool(problems), cv.FINDING_TRAINING_VIEW_INVALID, "; ".join(problems))
    cv.refuse_when(
        contains_hidden_reasoning_key(view),
        cv.FINDING_TRAINING_VIEW_INVALID,
        "training_view carries a hidden-reasoning key",
    )


def _reason_codes(variant: str, success: bool) -> list[str]:
    codes = []
    if variant != cv.VARIANT_GOLD:
        codes.append(f"tool_world.variant.{variant}")
    if not success:
        codes.append("tool_world.predicate_fail")
    return codes


def build_record(
    env: Any, trajectory: Any, *, catalog_sha256: str, run_id: str, policy: str, draw: int
) -> dict[str, Any]:
    """The record for one finished trajectory; ``env`` must be the environment that produced it."""
    task, pack = env.task, env.pack
    verdict = env.verdict()
    success = bool(verdict["success"])
    identifier = record_id(pack.pack_sha256, policy, env.seed, draw)
    meta = {
        "factory": task.factory,
        "generator": cv.GENERATOR_NAME,
        "generator_version": cv.GENERATOR_VERSION,
        "generator_kind": cv.GENERATOR_KIND,
        "kind": "episode",
        "family": cv.FAMILY,
        "surface": task.surface,
        "variant": trajectory.variant,
        "seed": env.seed,
        "designed": True,
    }
    view = training_view(identifier, task, trajectory, success, meta)
    _check_training_view(view)
    replay_digest = env.replay_digest()
    accepted = success and trajectory.variant == cv.VARIANT_GOLD
    engine = env.fault_engine
    return {
        "schema_version": cv.RECORD_SCHEMA_VERSION,
        "record_kind": cv.RECORD_KIND_BY_SURFACE[task.surface],
        "family": cv.FAMILY,
        "id": identifier,
        "task_author": {
            "model": cv.TASK_AUTHOR_MODEL,
            "version": pack.pack_sha256,
            "prompt_hash": f"sha256:{task.spec_sha256}",
            "run_id": run_id,
        },
        "solver": {
            "model": cv.GENERATOR_NAME,
            "version": policy,
            "tool_policy": f"{task.surface}-{trajectory.variant}",
            "run_id": run_id,
            "outcome": cv.OUTCOME_SUCCESS if success else cv.OUTCOME_FAILURE,
        },
        "oracle": {
            "kind": cv.ORACLE_KIND,
            "status": "validated",
            "repo_commit": pack.pack_sha256,
            "command": f"python3 pipelines/tool_world_cli.py replay --record {identifier}",
            "result_hash": f"sha256:{replay_digest}",
            "certifier": cv.ORACLE_CERTIFIER,
            "signals": [
                "deterministic_environment",
                "replay_agreement",
                "predicate_pass" if success else "predicate_fail",
            ],
        },
        "curation": {
            "pipeline_version": cv.CURATION_PIPELINE_VERSION,
            "decision": cv.DECISION_ACCEPT if accepted else cv.DECISION_MEASURE,
            "reason_codes": _reason_codes(trajectory.variant, success),
        },
        "environment": {
            "repo_snapshot_hash": f"sha256:{pack.pack_sha256}",
            "repo_pack_id": pack.pack_id,
            "task_id": task.task_id,
            "catalog_sha256": catalog_sha256,
            "pack_id": pack.pack_id,
            "pack_sha256": pack.pack_sha256,
            "seed": env.seed,
            "surfaces": list(task.surfaces),
            "max_steps": task.max_steps,
        },
        "payload": {
            "task_specification": task.goal,
            "actions": [event.row() for event in env.events],
            "final_state_digest": env.snapshot_digest(),
            "predicate_results": {"public": verdict["public"], "hidden": verdict["hidden"]},
            "execution_evidence": {
                "replay_digest": replay_digest,
                "faults_armed": list(engine.armed_ids()),
                "faults_fired": list(engine.fired),
                "faults_recovered": trajectory.faults_recovered,
                "gave_up": trajectory.gave_up,
            },
            "outcome": cv.OUTCOME_SUCCESS if success else cv.OUTCOME_FAILURE,
        },
        "training_view": view,
    }


def record_digest(record: Mapping[str, Any]) -> str:
    return sha256_canonical(record)


bind_import_twin(__name__)
