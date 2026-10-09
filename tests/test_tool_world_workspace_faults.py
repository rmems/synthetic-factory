#!/usr/bin/env python3
"""Workspace fault kinds, their refusals at build time, and seeded determinism."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tool_world_test_support import cv, env_mod, load_pack, refusal
from tool_world_workspace_support import (
    COUNTER,
    DELETE_LOCK,
    EAGAIN,
    GET_ANCHOR,
    LOCK,
    PACK,
    RENAME,
    SUB_METHOD,
    TASKS,
    TRUNCATED_TAIL,
    add_sub,
    call,
    fault_env,
    plain_env,
    run_task,
    step,
)

# The support modules go first: they put pipelines/ on sys.path for the import below.
# isort: split
from tool_world.surfaces import workspace as workspace_mod


class FaultTests(unittest.TestCase):
    def test_transient_error_fires_once_on_the_matching_call_and_changes_nothing(self):
        env = fault_env("transient_error", "edit_file", {"path": COUNTER})
        surface = env.surface("workspace")
        before = surface.files[COUNTER]
        first = env.step(call("edit_file", path=COUNTER, old=GET_ANCHOR, new=SUB_METHOD))
        self.assertEqual(first.text, f"{EAGAIN} edit_file {COUNTER}; retry")
        self.assertEqual(first.fault_id, "test-transient_error")
        self.assertEqual(surface.files[COUNTER], before)
        second = env.step(call("edit_file", path=COUNTER, old=GET_ANCHOR, new=SUB_METHOD))
        self.assertTrue(second.text.startswith(f"edited {COUNTER}"), second.text)
        self.assertIsNone(second.fault_id)
        self.assertEqual(env.fault_engine.fired, ("test-transient_error",))

    def test_transient_error_names_the_suite_for_run_tests(self):
        env = fault_env("transient_error", "run_tests", {"suite": "unit"})
        self.assertEqual(step(env, "run_tests", suite="unit"), f"{EAGAIN} run_tests unit; retry")
        self.assertEqual(env.surface("workspace").test_runs, [])
        retried = step(env, "run_tests", suite="unit")
        self.assertEqual(retried.splitlines()[0], "unit: 1 passed, 2 failed")

    def test_selector_keeps_the_fault_off_other_paths(self):
        env = fault_env("transient_error", "read_file", {"path": COUNTER})
        self.assertTrue(step(env, "read_file", path=LOCK).startswith(f"{LOCK} ("))
        self.assertEqual(env.fault_engine.fired, ())
        self.assertTrue(step(env, "read_file", path=COUNTER).startswith(EAGAIN))

    def test_flaky_test_fails_the_named_case_once_then_passes(self):
        env = fault_env("flaky_test", "run_tests", {"suite": "unit"}, {"case": "add_exists"})
        add_sub(env)
        flaky = env.step(call("run_tests", suite="unit"))
        self.assertEqual(
            flaky.text,
            "unit: 2 passed, 1 failed\nFAIL add_exists: ETIMEDOUT after 30s (environment)",
        )
        self.assertEqual(flaky.fault_id, "test-flaky_test")
        self.assertEqual(step(env, "run_tests", suite="unit"), "unit: 3 passed, 0 failed")
        self.assertEqual(
            env.surface("workspace").test_runs,
            [{"suite": "unit", "failed": 1}, {"suite": "unit", "failed": 0}],
        )
        self.assertTrue(env.verdict()["hidden"]["tests_pass:suite=unit"])

    def test_truncated_output_cuts_an_unbounded_read_and_a_bounded_read_recovers(self):
        env = fault_env("truncated_output", "read_file", {"path": COUNTER})
        content = env.surface("workspace").files[COUNTER]
        self.assertGreater(len(content), workspace_mod._TRUNCATE_AT)
        cut = env.step(call("read_file", path=COUNTER))
        head = content[: workspace_mod._TRUNCATE_AT]
        self.assertEqual(cut.text, f"{COUNTER} ({len(content)} chars):\n{head}\n{TRUNCATED_TAIL}")
        self.assertEqual(cut.fault_id, "test-truncated_output")
        self.assertFalse(cut.truncated)
        recovered = step(env, "read_file", path=COUNTER, offset=0, limit=4000)
        self.assertEqual(recovered, f"{COUNTER} ({len(content)} chars, offset 0):\n{content}")

    def test_a_bounded_read_neither_counts_nor_fires_the_truncation(self):
        env = fault_env("truncated_output", "read_file", {"path": COUNTER})
        content = env.surface("workspace").files[COUNTER]
        bounded = env.step(call("read_file", path=COUNTER, limit=20))
        self.assertEqual(
            bounded.text, f"{COUNTER} ({len(content)} chars, offset 0):\n{content[:20]}"
        )
        self.assertIsNone(bounded.fault_id)
        self.assertEqual(env.fault_engine.fired, ())
        cut = env.step(call("read_file", path=COUNTER))
        self.assertEqual(cut.fault_id, "test-truncated_output")
        self.assertTrue(cut.text.endswith(TRUNCATED_TAIL), cut.text)

    def test_a_schema_invalid_call_neither_counts_nor_fires(self):
        env = fault_env("transient_error", "run_tests", {"suite": "unit"})
        malformed = env.step(call("run_tests", suite=7))
        self.assertTrue(malformed.text.startswith("error: invalid arguments for run_tests"))
        self.assertIsNone(malformed.fault_id)
        self.assertEqual(env.fault_engine.fired, ())
        self.assertTrue(step(env, "run_tests", suite="unit").startswith(EAGAIN))

    def test_a_fault_kind_the_surface_lacks_is_refused_when_the_environment_is_built(self):
        with refusal(self, cv.FINDING_FAULT_UNKNOWN, "no fault kind 'rate_limited'"):
            fault_env("rate_limited", "run_tests")

    def test_a_fault_no_observation_could_show_is_refused_when_the_environment_is_built(self):
        rows = (
            ("transient_error", "report_result", None, None, "names tool 'report_result'"),
            ("transient_error", "no_such_tool", None, None, "names tool 'no_such_tool'"),
            ("truncated_output", "edit_file", None, None, "only shows on read_file"),
            ("flaky_test", "read_file", None, {"case": "add_exists"}, "only shows on run_tests"),
            ("flaky_test", "run_tests", None, None, "needs params.case"),
            ("flaky_test", "run_tests", None, {"case": 7}, "needs params.case"),
            ("flaky_test", "run_tests", {"suite": "unit"}, {"case": "ghost"}, "suite(s) ['unit']"),
            ("flaky_test", "run_tests", None, {"case": "docs_updated"}, "['docs', 'unit']"),
            ("flaky_test", "run_tests", {"suite": "e2e"}, {"case": "add_exists"}, "suite 'e2e'"),
            ("flaky_test", "run_tests", {"suite": 3}, {"case": "add_exists"}, "names suite 3"),
        )
        for kind, tool, selector, params, needle in rows:
            with (
                self.subTest(kind=kind, tool=tool, selector=selector, params=params),
                refusal(self, cv.FINDING_FAULT_UNKNOWN, needle),
            ):
                fault_env(kind, tool, selector, params)

    def test_check_fault_accepts_every_committed_fault_row(self):
        surface = plain_env().surface("workspace")
        for task in load_pack(PACK).tasks:
            for spec in task.faults:
                with self.subTest(task=task.task_id, fault=spec.fault_id):
                    surface.check_fault(spec)


class DeterminismTests(unittest.TestCase):
    def test_state_view_is_sorted_and_deterministic(self):
        views = []
        for _ in range(2):
            env = plain_env(RENAME, seed=3)
            step(env, "write_file", path="zz.txt", content="z")
            step(env, "write_file", path="aa.txt", content="a")
            step(env, "run_tests", suite="config")
            views.append((env.surface("workspace").state_view(), env.snapshot_digest()))
        self.assertEqual(views[0], views[1])
        view = views[0][0]
        self.assertEqual(sorted(view), ["dirs", "files", "test_runs"])
        self.assertEqual(list(view["files"])[:2], ["README.md", "aa.txt"])
        self.assertEqual(view["test_runs"], [{"suite": "config", "failed": 3}])

    def test_same_seed_produces_identical_observation_digests(self):
        for task_id in TASKS:
            runs = []
            for _ in range(2):
                env, trajectory = run_task(task_id, 7)
                runs.append(
                    (
                        [event.observation_sha256 for event in env.events],
                        [item.observation for item in trajectory.steps],
                        env.replay_digest(),
                        env.snapshot_digest(),
                    )
                )
            with self.subTest(task=task_id):
                self.assertEqual(runs[0], runs[1])
                self.assertGreaterEqual(len(runs[0][0]), 5)

    def test_a_fifty_percent_fault_arms_under_some_seeds_and_not_others(self):
        pack = load_pack(PACK)
        task = pack.task(DELETE_LOCK)
        armed = {
            env_mod.Environment(pack, task, seed).fault_engine.armed_ids() for seed in range(20)
        }
        self.assertEqual(armed, {(), ("transient-list",)})


if __name__ == "__main__":
    unittest.main()
