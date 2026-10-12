#!/usr/bin/env python3
"""The rewrites of a generated record that fresh replay must detect or refuse.

Each table row is ``(label, mutate, needle)`` or ``(label, mutate, code,
needle)``: ``mutate`` edits a deep copy of a generated record in place, and
replay must then report a mismatch containing ``needle`` or raise the
refusal ``code`` whose prose contains ``needle``.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tool_world_record_support import HEX64, call

# The record support module goes first: it puts pipelines/ on sys.path for the import below.
# isort: split
from tool_world import vocabulary as cv

__all__ = [
    "EVIDENCE_TAMPERINGS",
    "LABEL_TAMPERINGS",
    "MALFORMED_RECORDS",
    "REPLAY_TAMPERINGS",
    "TRAINING_VIEW_TAMPERINGS",
    "UNBINDABLE_RECORDS",
]


def set_step(index: int, key: str, value):
    return lambda record: record["training_view"]["steps"][index].__setitem__(key, value)


def set_in(*path: str):
    def mutate(record: dict, value) -> None:
        target = record
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value

    return lambda value: lambda record: mutate(record, value)


def flip_predicate(record: dict) -> None:
    public = record["payload"]["predicate_results"]["public"]
    key = next(iter(public))
    public[key] = not public[key]


def flip_success(record: dict) -> None:
    reward = record["training_view"]["reward"]
    reward["success"] = not reward["success"]


# Rewrites that re-executing the recorded actions exposes.
REPLAY_TAMPERINGS = (
    (
        "observation text",
        set_step(0, "observation", "edited"),
        "step 1: training_view observation text differs",
    ),
    (
        "observation digest",
        lambda r: r["payload"]["actions"][0].__setitem__("observation_sha256", HEX64),
        "step 1: observation digest differs",
    ),
    (
        "fault id",
        lambda r: r["payload"]["actions"][0].__setitem__("fault_id", "ghost"),
        "differs from recorded 'ghost'",
    ),
    (
        "final state",
        set_in("payload", "final_state_digest")(HEX64),
        "final state digest differs",
    ),
    ("predicate results", flip_predicate, "predicate verdicts differ"),
    (
        "result hash",
        set_in("oracle", "result_hash")(f"sha256:{HEX64}"),
        "oracle.result_hash differs from the replay digest",
    ),
    ("reward.success", flip_success, "reward.success differs from the replayed verdict"),
    (
        "action arguments",
        lambda r: r["payload"]["actions"][0]["tool_call"].__setitem__("args", {"nonsense": True}),
        "step 1: observation digest differs",
    ),
    ("dropped step", lambda r: r["training_view"]["steps"].pop(), "training_view has"),
)
# Rewrites of the trainable projection the design says replay must detect.
TRAINING_VIEW_TAMPERINGS = (
    (
        "training_view tool_call",
        set_step(1, "tool_call", call("delete_file", path="README.md")),
        "step 2: training_view tool_call differs",
    ),
    (
        "training_view tool_call arguments",
        lambda r: r["training_view"]["steps"][0]["tool_call"]["args"].__setitem__(
            "pattern", "rm -rf /"
        ),
        "step 1: training_view tool_call differs",
    ),
    ("step number", set_step(0, "n", 9), "step 1: training_view step number differs"),
    ("hidden-reasoning key", set_step(0, "reasoning", "x"), "hidden-reasoning key"),
    (
        "empty decision basis",
        set_step(0, "decision_basis", ""),
        "decision_basis must be a non-empty",
    ),
    (
        "decision basis text",
        set_step(0, "decision_basis", "Plan: just do it now"),
        "the scripted policy replays a different gold trajectory",
    ),
    (
        "outcome text",
        set_in("training_view", "outcome")("Failed: everything broke"),
        "training_view.outcome differs from the replayed value",
    ),
    ("goal", set_in("training_view", "goal")("do something else"), "training_view.goal differs"),
    (
        "cost_steps",
        set_in("training_view", "reward", "cost_steps")(99),
        "reward.cost_steps differs",
    ),
    ("meta seed", set_in("training_view", "meta", "seed")(5), "training_view.meta.seed differs"),
    (
        "meta generator",
        set_in("training_view", "meta", "generator")("other-generator"),
        "training_view.meta.generator differs",
    ),
    (
        "meta generator_version",
        set_in("training_view", "meta", "generator_version")("9.9"),
        "training_view.meta.generator_version differs",
    ),
    (
        "meta generator_kind",
        set_in("training_view", "meta", "generator_kind")("hosted"),
        "training_view.meta.generator_kind differs",
    ),
    (
        "training_view id",
        set_in("training_view", "id")("twd-other-00001"),
        "training_view.id differs",
    ),
)
# Relabels of who proposed and how the record was curated.
LABEL_TAMPERINGS = (
    ("decision", set_in("curation", "decision")("measure"), "curation.decision differs"),
    ("reason codes", set_in("curation", "reason_codes")(["x"]), "curation.reason_codes differs"),
    (
        "tool policy",
        set_in("solver", "tool_policy")("workspace-skip_verification"),
        "solver.tool_policy differs",
    ),
    ("solver outcome", set_in("solver", "outcome")("failure"), "solver.outcome differs"),
    ("record id", set_in("id")("twd-forged-00001"), "id differs from the replayed value"),
)
# Forged execution evidence and binding.
EVIDENCE_TAMPERINGS = (
    (
        "payload action row",
        lambda r: r["payload"]["actions"][0].__setitem__("truncated", True),
        "step 1: payload action row differs from the replayed event",
    ),
    (
        "task specification",
        set_in("payload", "task_specification")("x"),
        "payload.task_specification differs",
    ),
    (
        "faults fired",
        set_in("payload", "execution_evidence", "faults_fired")([]),
        "faults_fired differs",
    ),
    (
        "faults armed",
        set_in("payload", "execution_evidence", "faults_armed")(["ghost"]),
        "faults_armed differs",
    ),
    (
        "gave up",
        set_in("payload", "execution_evidence", "gave_up")(True),
        "gave_up or faults_recovered differ from the scripted policy's run",
    ),
    (
        "faults recovered",
        set_in("payload", "execution_evidence", "faults_recovered")(9),
        "faults_recovered differs",
    ),
    ("payload outcome", set_in("payload", "outcome")("failure"), "payload.outcome differs"),
    (
        "catalog digest",
        set_in("environment", "catalog_sha256")(HEX64),
        "environment.catalog_sha256 differs",
    ),
    ("oracle signals", set_in("oracle", "signals")([]), "oracle.signals differs"),
)
# Records the catalog cannot bind to a pack, task and seed.
UNBINDABLE_RECORDS = (
    (
        "pack digest",
        set_in("environment", "pack_sha256")(HEX64),
        cv.FINDING_PACK_SHA_MISMATCH,
        "generated from pack digest",
    ),
    (
        "pack id",
        set_in("environment", "pack_id")("nope"),
        cv.FINDING_PACK_FILE_MISSING,
        "'nope' is not in catalog",
    ),
    (
        "task id",
        set_in("environment", "task_id")("counter.nope"),
        cv.FINDING_TASK_NOT_FOUND,
        "'counter.nope'",
    ),
    ("seed", set_in("environment", "seed")(-1), cv.FINDING_SEED_INVALID, "seed must lie"),
)
# Records whose shape replay refuses before binding them.
MALFORMED_RECORDS = (
    ("schema version", set_in("schema_version")("other"), "schema_version must be"),
    ("missing actions", lambda r: r["payload"].pop("actions"), "record lacks payload.actions"),
    ("missing environment", lambda r: r.pop("environment"), "record lacks environment.pack_id"),
    ("actions not a list", set_in("payload", "actions")({}), "actions and steps must be lists"),
    (
        "action without tool_call",
        lambda r: r["payload"]["actions"].__setitem__(0, {"n": 1}),
        "actions[0] must carry a tool_call",
    ),
    (
        "too many actions",
        lambda r: r["payload"].__setitem__("actions", r["payload"]["actions"] * 20),
        "exceed max_steps",
    ),
    (
        "steps not objects",
        set_in("training_view", "steps")(["x"]),
        "training_view.steps[0] must be an object",
    ),
    (
        "reward not an object",
        set_in("training_view", "reward")("x"),
        "training_view.reward must be an object",
    ),
    (
        "variant undeclared",
        set_in("training_view", "meta", "variant")("skip_tests"),
        "variant 'skip_tests' is neither gold nor a perturbation",
    ),
    ("id without a draw", set_in("id")("twd-x"), "id must end in the draw number"),
    (
        "gave_up not a bool",
        set_in("payload", "execution_evidence", "gave_up")("no"),
        "payload.execution_evidence.gave_up must be bool",
    ),
    ("solver version not a string", set_in("solver", "version")(7), "solver.version must be str"),
    ("missing oracle", lambda r: r.pop("oracle"), "record lacks oracle"),
    ("curation not an object", set_in("curation")([]), "curation must be an object"),
)
