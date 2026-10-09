#!/usr/bin/env python3
"""Assemble one trajectory into a tool-world record.

The record separates who proposed (``solver``), what was proposed and
observed (``payload.actions``), what the environment decided (``oracle``,
``payload.predicate_results``), and the trainable projection
(``training_view``, the repository episode envelope). The training view is
validated by the repository's own episode gate with hidden thought forbidden
and terminal outcome enforced; a record that fails it is refused, not fixed.
Every block builder here is also what replay re-derives a record from.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from . import vocabulary as cv
from ._contract import (
    bind_import_twin,
    check_episode,
    contains_hidden_reasoning_key,
    sha256_canonical,
)

__all__ = [
    "RunContext",
    "build_record",
    "check_training_view",
    "curation",
    "environment",
    "oracle",
    "outcome_text",
    "payload",
    "reason_codes",
    "record_id",
    "solver",
    "task_author",
    "training_meta",
    "training_view",
]

_GAVE_UP_TEXT = "Failed: gave up after the first fault instead of recovering"


@dataclass(frozen=True)
class RunContext:
    """What the run contributes to every record: the catalog pin, the run id, the policy digest."""

    catalog_sha256: str
    run_id: str
    policy: str


def record_id(pack_sha256: str, policy_sha256: str, seed: int, draw: int) -> str:
    return f"{cv.RECORD_ID_PREFIX}-{pack_sha256[:16]}-{policy_sha256[:16]}-{seed}-{draw:05d}"


def outcome_text(title: str, success: bool, gave_up: bool) -> str:
    """Prose ending with the verdict, so a title such as "... suite passes" cannot flip it."""
    if success:
        return f"Succeeded: {title}"
    if gave_up:
        return _GAVE_UP_TEXT
    return f"Failed: {title}; a goal predicate failed"


def training_meta(task: Any, variant: str, seed: int) -> dict[str, Any]:
    return {
        "factory": task.factory,
        "generator": cv.GENERATOR_NAME,
        "generator_version": cv.GENERATOR_VERSION,
        "generator_kind": cv.GENERATOR_KIND,
        "kind": "episode",
        "family": cv.FAMILY,
        "surface": task.surface,
        "variant": variant,
        "seed": seed,
        "designed": True,
    }


def training_view(identifier: str, env: Any, trajectory: Any, success: bool) -> dict[str, Any]:
    task = env.task
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
        "outcome": outcome_text(task.title, success, trajectory.gave_up),
        "reward": {
            "success": success,
            "cost_steps": len(steps),
            "faults_recovered": trajectory.faults_recovered,
        },
        "meta": training_meta(task, trajectory.variant, env.seed),
    }


def check_training_view(view: Mapping[str, Any]) -> None:
    """The episode gate with hidden thought forbidden and the terminal outcome enforced."""
    problems = check_episode(
        view, "training_view", forbid_hidden_thought=True, enforce_terminal_outcome=True
    )
    cv.refuse_when(bool(problems), cv.FINDING_TRAINING_VIEW_INVALID, "; ".join(problems))
    cv.refuse_when(
        contains_hidden_reasoning_key(view),
        cv.FINDING_TRAINING_VIEW_INVALID,
        "training_view carries a hidden-reasoning key",
    )


def reason_codes(variant: str, success: bool) -> list[str]:
    codes = []
    if variant != cv.VARIANT_GOLD:
        codes.append(f"tool_world.variant.{variant}")
    if not success:
        codes.append("tool_world.predicate_fail")
    return codes


def task_author(pack: Any, task: Any, run_id: str) -> dict[str, Any]:
    return {
        "model": cv.TASK_AUTHOR_MODEL,
        "version": pack.pack_sha256,
        "prompt_hash": f"sha256:{task.spec_sha256}",
        "run_id": run_id,
    }


def solver(task: Any, variant: str, run: RunContext, success: bool) -> dict[str, Any]:
    return {
        "model": cv.GENERATOR_NAME,
        "version": run.policy,
        "tool_policy": f"{task.surface}-{variant}",
        "run_id": run.run_id,
        "outcome": cv.OUTCOME_SUCCESS if success else cv.OUTCOME_FAILURE,
    }


def oracle(pack: Any, identifier: str, replay_digest: str, success: bool) -> dict[str, Any]:
    return {
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
    }


def curation(variant: str, success: bool) -> dict[str, Any]:
    accepted = success and variant == cv.VARIANT_GOLD
    return {
        "pipeline_version": cv.CURATION_PIPELINE_VERSION,
        "decision": cv.DECISION_ACCEPT if accepted else cv.DECISION_MEASURE,
        "reason_codes": reason_codes(variant, success),
    }


def environment(env: Any, catalog_sha256: str) -> dict[str, Any]:
    pack, task = env.pack, env.task
    return {
        "repo_snapshot_hash": f"sha256:{pack.pack_sha256}",
        "repo_pack_id": pack.pack_id,
        "task_id": task.task_id,
        "catalog_sha256": catalog_sha256,
        "pack_id": pack.pack_id,
        "pack_sha256": pack.pack_sha256,
        "seed": env.seed,
        "surfaces": list(task.surfaces),
        "max_steps": task.max_steps,
    }


def payload(
    env: Any, trajectory: Any, verdict: Mapping[str, Any], replay_digest: str
) -> dict[str, Any]:
    engine = env.fault_engine
    success = bool(verdict["success"])
    return {
        "task_specification": env.task.goal,
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
    }


def build_record(env: Any, trajectory: Any, run: RunContext, draw: int) -> dict[str, Any]:
    """The record for one finished trajectory; ``env`` must be the environment that produced it."""
    task, pack, variant = env.task, env.pack, trajectory.variant
    verdict = env.verdict()
    success = bool(verdict["success"])
    identifier = record_id(pack.pack_sha256, run.policy, env.seed, draw)
    view = training_view(identifier, env, trajectory, success)
    check_training_view(view)
    replay_digest = env.replay_digest()
    return {
        "schema_version": cv.RECORD_SCHEMA_VERSION,
        "record_kind": cv.RECORD_KIND_BY_SURFACE[task.surface],
        "family": cv.FAMILY,
        "id": identifier,
        "task_author": task_author(pack, task, run.run_id),
        "solver": solver(task, variant, run, success),
        "oracle": oracle(pack, identifier, replay_digest, success),
        "curation": curation(variant, success),
        "environment": environment(env, run.catalog_sha256),
        "payload": payload(env, trajectory, verdict, replay_digest),
        "training_view": view,
    }


def record_digest(record: Mapping[str, Any]) -> str:
    return sha256_canonical(record)


bind_import_twin(__name__)
