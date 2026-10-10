#!/usr/bin/env python3
"""The record builder: the training view, its actors and the verdict of one scripted episode.

The record builder is the only writer of a training view; each test runs
the scripted policy on the committed ``counter-workspace`` pack and reads
the record it assembles.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tool_world_record_support import (
    ADD_SUB,
    DELETE_LOCK,
    FACTORY,
    HEX64,
    PACK,
    RECORD_ID,
    build,
    call,
    episode,
    gate,
    refusal,
    task_variant,
)

# The support module goes first: it puts pipelines/ on sys.path for the imports below.
# isort: split
from tool_world import env as env_mod
from tool_world import records
from tool_world import vocabulary as cv
from tool_world._contract import contains_hidden_reasoning_key, sha256_bytes
from tool_world.policies import scripted


class GoldRecord(unittest.TestCase):
    """One gold episode on the add-sub task, read section by section."""

    def setUp(self):
        self.env, _trajectory, self.record = episode(ADD_SUB)
        self.view = self.record["training_view"]

    def test_the_training_view_passes_the_episode_gate(self):
        view = self.view
        self.assertEqual(gate(view), [])
        self.assertFalse(contains_hidden_reasoning_key(self.record))
        self.assertIs(view["reward"]["success"], True)
        self.assertEqual(view["outcome"], f"Succeeded: {self.env.task.title}")
        self.assertEqual(view["reward"], {"success": True, "cost_steps": 7, "faults_recovered": 2})
        self.assertRegex(self.record["id"], RECORD_ID)
        self.assertEqual(self.record["id"], view["id"])
        self.assertEqual(
            (self.record["schema_version"], self.record["record_kind"], self.record["family"]),
            (cv.RECORD_SCHEMA_VERSION, "tool_episode_v1", cv.FAMILY),
        )

    def test_the_task_author_and_the_solver_are_separate_actors(self):
        task, pack = self.env.task, self.env.pack
        self.assertEqual(
            self.record["task_author"],
            {
                "model": cv.TASK_AUTHOR_MODEL,
                "version": pack.pack_sha256,
                "prompt_hash": f"sha256:{task.spec_sha256}",
                "run_id": "twd-run-test",
            },
        )
        self.assertEqual(
            self.record["solver"],
            {
                "model": cv.GENERATOR_NAME,
                "version": scripted.policy_sha256(),
                "tool_policy": "workspace-gold",
                "run_id": "twd-run-test",
                "outcome": cv.OUTCOME_SUCCESS,
            },
        )

    def test_the_oracle_and_the_curation_carry_the_replay_verdict(self):
        self.assertEqual(
            self.record["oracle"],
            {
                "kind": cv.ORACLE_KIND,
                "status": "validated",
                "repo_commit": self.env.pack.pack_sha256,
                "command": (
                    "python3 pipelines/tool_world_cli.py replay <run_dir> "
                    f"--record {self.record['id']}"
                ),
                "result_hash": f"sha256:{self.env.replay_digest()}",
                "certifier": cv.ORACLE_CERTIFIER,
                "signals": ["deterministic_environment", "replay_agreement", "predicate_pass"],
            },
        )
        self.assertEqual(
            self.record["curation"],
            {
                "pipeline_version": cv.CURATION_PIPELINE_VERSION,
                "decision": "accept",
                "reason_codes": [],
            },
        )

    def test_the_environment_and_the_meta_pin_the_pack_and_the_draw(self):
        task, pack = self.env.task, self.env.pack
        self.assertEqual(
            self.record["environment"],
            {
                "repo_snapshot_hash": f"sha256:{pack.pack_sha256}",
                "repo_pack_id": PACK,
                "task_id": ADD_SUB,
                "catalog_sha256": HEX64,
                "pack_id": PACK,
                "pack_sha256": pack.pack_sha256,
                "seed": 1,
                "surfaces": ["workspace"],
                "max_steps": task.max_steps,
            },
        )
        self.assertEqual(
            self.view["meta"],
            {
                "factory": FACTORY,
                "generator": cv.GENERATOR_NAME,
                "generator_version": cv.GENERATOR_VERSION,
                "generator_kind": cv.GENERATOR_KIND,
                "kind": "episode",
                "family": cv.FAMILY,
                "surface": "workspace",
                "variant": "gold",
                "seed": 1,
                "designed": True,
            },
        )


class RecordShape(unittest.TestCase):
    def test_the_payload_is_the_event_log_and_the_environment_verdict(self):
        env, _trajectory, record = episode(ADD_SUB)
        payload = record["payload"]
        self.assertEqual(payload["task_specification"], env.task.goal)
        self.assertEqual(payload["actions"], [event.row() for event in env.events])
        self.assertEqual(payload["final_state_digest"], env.snapshot_digest())
        verdict = env.verdict()
        self.assertEqual(
            payload["predicate_results"], {"public": verdict["public"], "hidden": verdict["hidden"]}
        )
        self.assertEqual(
            payload["execution_evidence"],
            {
                "replay_digest": env.replay_digest(),
                "faults_armed": ["transient-tests", "truncated-read"],
                "faults_fired": ["transient-tests", "truncated-read"],
                "faults_recovered": 2,
                "gave_up": False,
            },
        )
        self.assertEqual(payload["outcome"], cv.OUTCOME_SUCCESS)
        steps = record["training_view"]["steps"]
        self.assertEqual([step["n"] for step in steps], list(range(1, 8)))
        self.assertEqual(
            [step["tool_call"] for step in steps], [row["tool_call"] for row in payload["actions"]]
        )
        self.assertEqual(
            [sha256_bytes(step["observation"].encode("utf-8")) for step in steps],
            [row["observation_sha256"] for row in payload["actions"]],
        )

    def test_a_failed_variant_is_measured_with_the_predicate_fail_reason(self):
        env, _trajectory, record = episode(DELETE_LOCK, variant="skip_confirmation")
        view = record["training_view"]
        self.assertEqual(gate(view), [])
        self.assertIs(view["reward"]["success"], False)
        self.assertEqual(view["outcome"], f"Failed: {env.task.title}; a goal predicate failed")
        self.assertEqual(
            record["curation"]["reason_codes"],
            ["tool_world.variant.skip_confirmation", "tool_world.predicate_fail"],
        )
        self.assertEqual(record["curation"]["decision"], cv.DECISION_MEASURE)
        self.assertEqual(record["solver"]["outcome"], cv.OUTCOME_FAILURE)
        self.assertEqual(record["solver"]["tool_policy"], "workspace-skip_confirmation")
        self.assertEqual(record["oracle"]["signals"][-1], "predicate_fail")
        self.assertEqual(record["payload"]["outcome"], cv.OUTCOME_FAILURE)
        hidden = record["payload"]["predicate_results"]["hidden"]
        self.assertFalse(hidden["no_irreversible_without_confirmation"])

    def test_a_successful_perturbed_variant_is_measured_not_accepted(self):
        _env, trajectory, record = episode(
            ADD_SUB, variant="skip_verification", perturbations=("skip_verification",), faults=()
        )
        self.assertIs(record["training_view"]["reward"]["success"], True)
        self.assertEqual(record["curation"]["decision"], cv.DECISION_MEASURE)
        self.assertEqual(
            record["curation"]["reason_codes"], ["tool_world.variant.skip_verification"]
        )
        self.assertEqual(record["oracle"]["signals"][-1], "predicate_pass")
        self.assertEqual(trajectory.variant, "skip_verification")

    def test_the_give_up_record_names_the_abandoned_recovery(self):
        env, trajectory, record = episode(ADD_SUB, variant="give_up_on_fault")
        self.assertTrue(trajectory.gave_up)
        self.assertEqual(
            record["training_view"]["outcome"],
            f"Failed: {env.task.title}; gave up after the first fault instead of recovering, "
            "so the goal failed",
        )
        self.assertIs(record["training_view"]["reward"]["success"], False)
        self.assertTrue(record["payload"]["execution_evidence"]["gave_up"])
        self.assertEqual(gate(record["training_view"]), [])

    def test_record_id_format(self):
        self.assertEqual(
            records.record_id("a" * 64, "b" * 64, 5, 3), f"twd-{'a' * 16}-{'b' * 16}-5-00003"
        )

    def test_the_builder_refuses_a_training_view_the_gate_rejects(self):
        pack, task = task_variant(ADD_SUB, faults=())
        cases = (
            ("", call("read_file", path="src/counter.py"), "decision_basis must be a non-empty"),
            ("Plan: read the file", call("read_file", path="x", thought="h"), "hidden-reasoning"),
            (
                "Plan: read the file",
                call("read_file", path="x", reasoning="h"),
                "hidden-reasoning key",
            ),
        )
        for basis, tool_call, needle in cases:
            env = env_mod.Environment(pack, task, 0)
            observation = env.step(tool_call)
            step = scripted.Step(1, basis, tool_call, observation.text, None)
            trajectory = scripted.Trajectory("gold", (step,), False, 0)
            with (
                self.subTest(needle=needle),
                refusal(self, cv.FINDING_TRAINING_VIEW_INVALID, needle),
            ):
                build(env, trajectory)


if __name__ == "__main__":
    unittest.main()
