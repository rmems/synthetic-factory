#!/usr/bin/env python3
"""Gold plans, perturbed variants, and seeded generation with fresh replay on the workspace pack."""

import contextlib
import copy
import io
import itertools
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tool_world_test_support import (
    PRODUCED_AT,
    catalog_mod,
    cv,
    env_mod,
    load_pack,
    private_catalog,
)
from tool_world_workspace_support import (
    ADD_SUB,
    COUNTER,
    DELETE_LOCK,
    DOCUMENT,
    EAGAIN,
    FACTORY,
    FIRED,
    GOLD_DELETE,
    LOCK,
    MEASURED,
    NO_CONFIRMATION,
    NOTE,
    PACK,
    RENAME,
    RENAMED_CONFIG_SHA256,
    SEEDS,
    TAMPERINGS,
    TASKS,
    build_record,
    call,
    names,
    plain_env,
    run_task,
    step,
)

# The support modules go first: they put pipelines/ on sys.path for the imports below.
# isort: split
from tool_world import cli, generate, replay
from tool_world._contract import contains_hidden_reasoning_key, load_strict_json
from tool_world.policies import scripted


class GoldTrajectoryTests(unittest.TestCase):
    def setUp(self):
        self.pack = load_pack(PACK)

    def test_every_gold_plan_succeeds_under_every_seed(self):
        for task in self.pack.tasks:
            for seed in SEEDS:
                with self.subTest(task=task.task_id, seed=seed):
                    env = env_mod.Environment(self.pack, task, seed)
                    trajectory = scripted.run(env)
                    self.assertTrue(env.verdict()["success"], env.verdict())
                    self.assertEqual(env.reported, task.gold[-1].tool_call["args"]["value"])
                    self.assertLessEqual(len(trajectory.steps), task.max_steps)
                    self.assertFalse(trajectory.gave_up)
                    self.assertEqual(trajectory.faults_recovered, len(env.fault_engine.fired))

    def test_every_declared_fault_fires_and_is_recovered_under_some_seed(self):
        for task in self.pack.tasks:
            for spec in task.faults:
                with self.subTest(task=task.task_id, fault=spec.fault_id):
                    self.assertTrue(self._fires_and_recovers(task, spec.fault_id))

    def _fires_and_recovers(self, task, fault_id: str) -> bool:
        for seed in range(20):
            env = env_mod.Environment(self.pack, task, seed)
            trajectory = scripted.run(env)
            if fault_id in env.fault_engine.fired:
                return env.verdict()["success"] and trajectory.faults_recovered >= 1
        return False

    def test_add_sub_gold_retries_the_transient_and_rereads_after_the_truncation(self):
        env, trajectory = run_task(ADD_SUB, 1)
        self.assertEqual(
            names(trajectory),
            [
                "run_tests",
                "run_tests",
                "read_file",
                "read_file",
                "edit_file",
                "run_tests",
                "report_result",
            ],
        )
        self.assertEqual(env.fault_engine.fired, ("transient-tests", "truncated-read"))
        self.assertEqual(trajectory.faults_recovered, 2)
        retry = trajectory.steps[1].decision_basis
        self.assertTrue(retry.startswith("Observation: the observation reported 'EAGAIN"), retry)
        reread = trajectory.steps[3]
        self.assertTrue(reread.decision_basis.startswith("Observation: the read was truncated"))
        self.assertEqual(reread.tool_call["args"], {"path": COUNTER, "offset": 0, "limit": 4000})
        self.assertTrue(reread.observation.endswith("return self._value\n"))
        self.assertEqual(trajectory.steps[-2].observation, "unit: 3 passed, 0 failed")

    def test_rename_gold_retries_the_flaky_docs_case(self):
        env, trajectory = run_task(RENAME, 1)
        self.assertEqual(
            names(trajectory),
            ["search", "edit_file", "edit_file", "run_tests", "run_tests", "report_result"],
        )
        self.assertIn("FAIL docs_updated: ETIMEDOUT", trajectory.steps[3].observation)
        self.assertEqual(trajectory.steps[4].observation, "config: 3 passed, 0 failed")
        self.assertEqual(
            env.surface("workspace").files["config/settings.toml"].count("retry_limit"), 1
        )

    def test_delete_lock_gold_confirms_before_the_delete_and_verifies_after(self):
        env, trajectory = run_task(DELETE_LOCK, 1)
        self.assertEqual(
            names(trajectory),
            ["list_dir", "read_file", "confirm_action", "delete_file", "list_dir", "report_result"],
        )
        self.assertEqual(trajectory.steps[4].observation, "locks/:\n(empty)")
        self.assertEqual(env.unconfirmed_irreversible, 0)

    def test_document_timeout_gold_writes_the_note_after_a_transient_write(self):
        env, trajectory = run_task(DOCUMENT, 1)
        self.assertEqual(
            names(trajectory),
            [
                "search",
                "list_dir",
                "write_file",
                "write_file",
                "run_tests",
                "run_tests",
                "report_result",
            ],
        )
        self.assertEqual(
            trajectory.steps[0].observation, "1 matches:\nconfig/settings.toml:4: timeout_s = 5"
        )
        self.assertEqual(trajectory.steps[1].observation, "error: ENOENT no such directory: docs/")
        self.assertEqual(trajectory.steps[2].observation, f"{EAGAIN} write_file {NOTE}; retry")
        self.assertIn("FAIL note_names_value: ETIMEDOUT", trajectory.steps[4].observation)
        verdict = env.verdict()
        self.assertTrue(verdict["public"]["max_steps:n=9"])
        self.assertTrue(verdict["hidden"][f"file_exists:path={NOTE}"])
        self.assertIn("timeout_s = 5", env.surface("workspace").files[NOTE])

    def test_document_timeout_accepts_any_note_the_docs_suite_passes(self):
        env = plain_env(DOCUMENT)
        step(env, "write_file", path=NOTE, content="timeout_s = 5, from config/settings.toml\n")
        self.assertEqual(step(env, "run_tests", suite="docs"), "docs: 3 passed, 0 failed")
        step(env, "report_result", value="docs suite passes")
        verdict = env.verdict()
        self.assertTrue(verdict["success"], verdict)
        self.assertEqual(
            sorted(verdict["hidden"]), [f"file_exists:path={NOTE}", "tests_pass:suite=docs"]
        )

    def test_rename_pins_the_renamed_config_bytes_not_the_prose(self):
        label = f"file_sha256:path=config/settings.toml,sha256={RENAMED_CONFIG_SHA256}"
        env, _ = run_task(RENAME, 1)
        self.assertTrue(env.verdict()["hidden"][label])
        step(
            env, "edit_file", path="config/settings.toml", old="timeout_s = 5", new="timeout_s = 9"
        )
        verdict = env.verdict()
        self.assertFalse(verdict["hidden"][label])
        self.assertTrue(verdict["hidden"]["tests_pass:suite=config"])
        self.assertFalse(verdict["success"])


class PerturbationTests(unittest.TestCase):
    def test_skip_confirmation_fails_only_the_confirmation_predicate(self):
        for seed in SEEDS:
            env, trajectory = run_task(DELETE_LOCK, seed, cv.PERTURBATION_SKIP_CONFIRMATION)
            verdict = env.verdict()
            with self.subTest(seed=seed):
                self.assertNotIn("confirm_action", names(trajectory))
                self.assertFalse(trajectory.gave_up)
                self.assertFalse(verdict["success"])
                self.assertFalse(verdict["hidden"][NO_CONFIRMATION])
                self.assertTrue(verdict["hidden"][f"file_absent:path={LOCK}"])
                self.assertTrue(verdict["public"]["value_reported:value=stale lock removed"])
                self.assertEqual(env.unconfirmed_irreversible, 1)

    def test_give_up_on_fault_fails_exactly_when_a_fault_fired(self):
        seen = set()
        for task_id, seed in itertools.product(TASKS, SEEDS):
            env, trajectory = run_task(task_id, seed, cv.PERTURBATION_GIVE_UP)
            fired = bool(env.fault_engine.fired)
            seen.add(fired)
            with self.subTest(task=task_id, seed=seed):
                self.assertEqual(trajectory.gave_up, fired)
                self.assertEqual(env.verdict()["success"], not fired)
                if fired:
                    self.assertEqual(trajectory.faults_recovered, 0)
                    self.assertEqual(env.reported, scripted._GIVE_UP_TEXT)
                    self.assertEqual(names(trajectory)[-1], "report_result")
        self.assertEqual(seen, {True, False})

    def test_wrong_arg_type_is_corrected_and_still_succeeds(self):
        for task_id in (ADD_SUB, DOCUMENT):
            for seed in SEEDS:
                env, trajectory = run_task(task_id, seed, cv.PERTURBATION_WRONG_ARG_TYPE)
                first, second = trajectory.steps[0], trajectory.steps[1]
                with self.subTest(task=task_id, seed=seed):
                    tool = first.tool_call["name"]
                    self.assertTrue(
                        first.observation.startswith(f"error: invalid arguments for {tool}")
                    )
                    self.assertIsNone(first.fault_id)
                    self.assertEqual(second.tool_call["name"], tool)
                    self.assertIn(
                        "(first attempt sends the wrong argument type)", first.decision_basis
                    )
                    self.assertTrue(env.verdict()["success"])
                    self.assertEqual(len(trajectory.steps), 8)

    def test_skip_verification_drops_the_test_run_and_the_environment_still_passes(self):
        for seed in SEEDS:
            env, trajectory = run_task(DOCUMENT, seed, cv.PERTURBATION_SKIP_VERIFICATION)
            with self.subTest(seed=seed):
                self.assertNotIn("run_tests", names(trajectory))
                self.assertEqual(env.surface("workspace").verification_events, [])
                self.assertEqual(env.fault_engine.fired, ("transient-write",))
                self.assertTrue(env.verdict()["success"])

    def test_records_carry_the_environment_label_not_the_authors(self):
        env, gold = run_task(DELETE_LOCK, 1)
        record = build_record(env, gold)
        self.assertEqual(
            record["curation"],
            {"pipeline_version": "tool-world-v1", "decision": "accept", "reason_codes": []},
        )
        self.assertEqual(record["record_kind"], "tool_episode_v1")
        self.assertEqual(record["training_view"]["meta"]["factory"], FACTORY)
        self.assertEqual(
            record["training_view"]["outcome"],
            "Succeeded: remove the stale lock file with confirmation",
        )
        env, skipped = run_task(DELETE_LOCK, 1, cv.PERTURBATION_SKIP_CONFIRMATION)
        record = build_record(env, skipped, draw=2)
        self.assertEqual(record["curation"]["decision"], "measure")
        self.assertEqual(
            record["curation"]["reason_codes"],
            ["tool_world.variant.skip_confirmation", "tool_world.predicate_fail"],
        )
        self.assertEqual(record["solver"]["outcome"], "failure")
        self.assertFalse(record["payload"]["predicate_results"]["hidden"][NO_CONFIRMATION])
        env, gave_up = run_task(ADD_SUB, 1, cv.PERTURBATION_GIVE_UP)
        record = build_record(env, gave_up, draw=3)
        self.assertEqual(
            record["training_view"]["outcome"],
            f"Failed: {env.task.title}; gave up after the first fault instead of recovering, "
            "so the goal failed",
        )
        self.assertTrue(record["payload"]["execution_evidence"]["gave_up"])
        self.assertEqual(
            record["payload"]["execution_evidence"]["faults_fired"], ["transient-tests"]
        )


class GenerateReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = tempfile.TemporaryDirectory()
        root = Path(cls.scratch.name)
        cls.catalog_dir = private_catalog(root / "catalog", (PACK,))
        cls.run_dir = root / "run"
        request = generate.RunRequest(
            catalog_dir=cls.catalog_dir,
            out_dir=cls.run_dir,
            seed=1,
            count=len(TASKS),
            factory=FACTORY,
            produced_at=PRODUCED_AT,
        )
        cls.summary = generate.run(request)
        cls.catalog = catalog_mod.load_catalog(cls.catalog_dir)
        lines = (cls.run_dir / "candidates.jsonl").read_text().splitlines()
        cls.records = [load_strict_json(line) for line in lines]

    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()

    def record(self, task_id: str, variant: str) -> dict:
        """A deep copy of the generated record for ``task_id`` under ``variant``."""
        for record in self.records:
            meta = record["training_view"]["meta"]
            if record["environment"]["task_id"] == task_id and meta["variant"] == variant:
                return copy.deepcopy(record)
        self.fail(f"no record for {task_id} [{variant}]")

    def test_generate_and_replay_round_trip_on_a_private_catalog(self):
        expected = sum(1 + len(task.perturbations) for task in load_pack(PACK).tasks)
        summary = self.summary
        self.assertEqual((summary["accepted"], summary["records"]), (len(TASKS), expected))
        rows = {(row["task_id"], row["variant"]): row for row in summary["rows"]}
        self.assertEqual(rows[(ADD_SUB, "gold")]["faults_fired"], 2)
        self.assertFalse(rows[(DELETE_LOCK, "skip_confirmation")]["success"])
        measured = {row["decision"] for row in summary["rows"] if row["variant"] != "gold"}
        self.assertEqual(measured, {"measure"})
        result = replay.replay_run(self.run_dir, self.catalog)
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["records"], expected)
        self.assertEqual({record["record_kind"] for record in self.records}, {"tool_episode_v1"})
        self.assertFalse(any(contains_hidden_reasoning_key(record) for record in self.records))

    def detected(self, record: dict) -> bool:
        """Replay rejects the record: a mismatch row or a coded refusal, never agreement."""
        try:
            return not replay.replay_record(record, self.catalog).agreement
        except cv.ToolWorldRefusal:
            return True

    def test_every_tampering_of_the_label_or_the_projection_is_detected(self):
        measured = self.record(*MEASURED)
        self.assertEqual(measured["curation"]["decision"], "measure")
        self.assertTrue(measured["training_view"]["reward"]["success"])
        fired = self.record(*FIRED)
        self.assertEqual(len(fired["payload"]["execution_evidence"]["faults_fired"]), 2)
        steps = self.record(*GOLD_DELETE)["training_view"]["steps"]
        self.assertEqual(steps[3]["tool_call"], call("delete_file", path=LOCK))
        for label, (task_id, variant), mutate in TAMPERINGS:
            record = self.record(task_id, variant)
            self.assertFalse(self.detected(record), label)
            mutate(record)
            with self.subTest(label=label):
                self.assertTrue(self.detected(record), "replay agreed with a tampered record")

    def test_tools_command_lists_the_workspace_tools_with_their_schemas(self):
        with tempfile.TemporaryDirectory() as directory:
            catalog_dir = private_catalog(Path(directory) / "catalog", (PACK,))
            buffer = io.StringIO()
            argv = [
                "tools",
                "--catalog",
                str(catalog_dir),
                "--pack",
                PACK,
                "--task",
                ADD_SUB,
                "--json",
            ]
            with contextlib.redirect_stdout(buffer):
                code = cli.run(argv)
        self.assertEqual(code, 0)
        tools = {row["name"]: row for row in json.loads(buffer.getvalue())["tools"]}
        self.assertEqual(len(tools), 9)
        self.assertEqual(tools["edit_file"]["input_schema"]["required"], ["path", "old", "new"])
        self.assertTrue(tools["delete_file"]["irreversible"])
        self.assertEqual(
            tools["read_file"]["input_schema"]["properties"]["offset"],
            {"type": "integer", "minimum": 0},
        )
        self.assertFalse(tools["search"]["input_schema"]["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
