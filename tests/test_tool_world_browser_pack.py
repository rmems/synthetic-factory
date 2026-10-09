#!/usr/bin/env python3
"""The catalog-browser pack: header, fault coverage, gold plans, perturbations, and replay."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tool_world_browser_support import (
    LEGACY,
    PACK,
    PRICE,
    SAMPLE_SEEDS,
    SEARCH,
    TASKS,
    firing_env,
    gold_run,
    quiet_env,
)
from tool_world_test_support import (
    CATALOG_DIR,
    PRODUCED_AT,
    catalog_mod,
    cv,
    load_pack,
    make_env,
    private_catalog,
)

# The support modules go first: they put pipelines/ on sys.path for the imports below.
# isort: split
from tool_world import generate, replay
from tool_world._contract import contains_hidden_reasoning_key, load_strict_json
from tool_world.policies import scripted
from tool_world.surfaces import browser as browser_mod

GOLD_SEEDS = range(60)


def firing_gold_run(task_id: str, fault_id: str):
    """``(seed, env, trajectory)`` of the first gold run whose seed fires ``fault_id``, or None."""
    for seed in GOLD_SEEDS:
        env, trajectory = gold_run(task_id, seed)
        if fault_id in env.fault_engine.fired:
            return seed, env, trajectory
    return None


def quiet_marker_sightings(task, seed: int) -> list[tuple[str, int, str]]:
    """Markers of faults that did not fire under ``seed`` yet appear in a gold observation."""
    env, trajectory = gold_run(task.task_id, seed)
    quiet = [spec for spec in task.faults if spec.fault_id not in env.fault_engine.fired]
    return [
        (task.task_id, seed, spec.fault_id)
        for step in trajectory.steps
        for spec in quiet
        if spec.marker in step.observation
    ]


class CatalogBrowserPackTests(unittest.TestCase):
    def test_pack_header_license_and_size(self):
        pack = load_pack(PACK)
        counter = load_strict_json((CATALOG_DIR / "counter-workspace" / "PACK.json").read_text())
        self.assertEqual(pack.surfaces, (cv.SURFACE_BROWSER,))
        self.assertEqual(pack.license, counter["license"])
        self.assertEqual({task.factory for task in pack.tasks}, {"tool-world-browser-factory"})
        self.assertEqual(sorted(task.task_id for task in pack.tasks), sorted(TASKS))
        total = sum(path.stat().st_size for path in pack.directory.rglob("*") if path.is_file())
        self.assertLess(total, 60_000)

    def test_tasks_cover_every_fault_kind_and_carry_no_hidden_reasoning(self):
        pack = load_pack(PACK)
        kinds = {spec.kind for task in pack.tasks for spec in task.faults}
        self.assertEqual(kinds, browser_mod.BrowserSurface.FAULT_KINDS)
        for path in sorted((pack.directory / "tasks").glob("*.json")):
            self.assertFalse(
                contains_hidden_reasoning_key(load_strict_json(path.read_text())), path.name
            )
        self.assertTrue(all(task.perturbations for task in pack.tasks))

    def test_gold_plans_succeed_for_the_sample_seeds(self):
        for task_id in TASKS:
            for seed in SAMPLE_SEEDS:
                env, trajectory = gold_run(task_id, seed)
                verdict = env.verdict()
                self.assertTrue(verdict["success"], (task_id, seed, verdict))
                self.assertFalse(trajectory.gave_up)
                self.assertLessEqual(len(trajectory.steps), env.task.max_steps)

    def test_every_fault_fires_and_is_recovered_in_a_gold_trajectory(self):
        for task in load_pack(PACK).tasks:
            for spec in task.faults:
                found = firing_gold_run(task.task_id, spec.fault_id)
                self.assertIsNotNone(found, f"{spec.fault_id} never fired in 60 gold seeds")
                seed, env, trajectory = found
                self.assertTrue(env.verdict()["success"], (task.task_id, spec.fault_id, seed))
                self.assertGreaterEqual(trajectory.faults_recovered, 1)

    def test_perturbed_variants_are_labelled_by_the_environment(self):
        env = make_env(PACK, LEGACY, firing_env(LEGACY, "legacy-redirect-loop", "/catalog").seed)
        trajectory = scripted.run(env, cv.PERTURBATION_GIVE_UP)
        self.assertTrue(trajectory.gave_up)
        self.assertIs(env.verdict()["success"], False)
        self.assertEqual(env.reported, scripted._GIVE_UP_TEXT)
        for task_id in (SEARCH, PRICE):
            env = quiet_env(task_id)
            scripted.run(env, cv.PERTURBATION_SKIP_VERIFICATION)
            verdict = env.verdict()
            self.assertFalse(verdict["success"])
            extracted = next(
                value for key, value in verdict["hidden"].items() if "extracted" in key
            )
            self.assertFalse(extracted)

    def test_wrong_arg_type_is_a_schema_error_the_gold_recovers_from(self):
        envs = (quiet_env(SEARCH), quiet_env(PRICE), make_env(PACK, LEGACY, 1))
        for env in envs:
            trajectory = scripted.run(env, cv.PERTURBATION_WRONG_ARG_TYPE)
            first = trajectory.steps[0]
            self.assertTrue(
                first.observation.startswith("error: invalid arguments for browser"), first
            )
            self.assertEqual((first.fault_id, env.events[0].fault_id), (None, None))
            self.assertEqual(first.tool_call["args"]["action"], 7)
            self.assertIs(env.verdict()["success"], True, env.task.task_id)
            self.assertEqual(len(env.events), len(trajectory.steps))

    def test_markers_appear_only_when_their_fault_fired(self):
        for task in load_pack(PACK).tasks:
            for seed in GOLD_SEEDS:
                self.assertEqual(quiet_marker_sightings(task, seed), [])

    def test_generate_and_replay_a_private_catalog_run(self):
        with tempfile.TemporaryDirectory() as temp:
            catalog_dir = private_catalog(Path(temp) / "catalog", (PACK,))
            out_dir = Path(temp) / "run"
            summary = generate.run(
                generate.RunRequest(
                    catalog_dir, out_dir, 1, 3, "tool-world-browser-factory", "all", PRODUCED_AT
                )
            )
            self.assertEqual((summary["records"], summary["accepted"]), (11, 3))
            golds = [row for row in summary["rows"] if row["variant"] == cv.VARIANT_GOLD]
            self.assertTrue(all(row["decision"] == cv.DECISION_ACCEPT for row in golds))
            report = replay.replay_run(out_dir, catalog_mod.load_catalog(catalog_dir))
            self.assertTrue(report["passed"], report)


if __name__ == "__main__":
    unittest.main()
