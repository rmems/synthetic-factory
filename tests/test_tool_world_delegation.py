#!/usr/bin/env python3
"""The delegation surface through the release-delegation pack: pack shape, refusals, workers."""

from __future__ import annotations

import dataclasses
import json
import unittest

from tests import tool_world_test_support as support
from tests.tool_world_delegation_support import (
    APP_PY,
    BRIEF,
    CHANGELOG,
    FACTORY,
    FEATURE_DEF,
    FEATURE_PY,
    PACK,
    SHIP,
    SMOKE,
    SMOKE_TEST,
    agent,
    declared_faults,
    fault_env,
    fault_row,
    files,
    plain_env,
    row_env,
    spawn,
    workers_env,
)

from curate_coding import contains_hidden_reasoning_key
from tool_world.policies import scripted
from tool_world.surfaces import delegation as delegation_mod


class PackTests(unittest.TestCase):
    def setUp(self):
        self.pack = support.load_pack(PACK)

    def test_pack_composes_delegation_over_workspace_with_three_roles(self):
        self.assertEqual(self.pack.surfaces, ("delegation", "workspace"))
        self.assertEqual(sorted(self.pack.workers), ["implementer", "scribe", "tester"])
        self.assertEqual(sorted(self.pack.tests), ["docs", "feature", "release", "smoke"])
        self.assertEqual({task.factory for task in self.pack.tasks}, {FACTORY})
        self.assertEqual({task.surfaces for task in self.pack.tasks}, {self.pack.surfaces})
        for role, spec in self.pack.workers.items():
            with self.subTest(role=role):
                self.assertIn("default", spec["profiles"])

    def test_license_block_is_the_counter_workspace_block_verbatim(self):
        self.assertEqual(self.pack.license, support.load_pack("counter-workspace").license)

    def test_pack_members_carry_no_hidden_reasoning_key_and_fit_the_budget(self):
        total = 0
        for path in sorted(self.pack.directory.rglob("*")):
            if not path.is_file():
                continue
            total += len(path.read_bytes())
            if path.suffix == ".json":
                payload = json.loads(path.read_text(encoding="utf-8"))
                self.assertFalse(contains_hidden_reasoning_key(payload), path)
        self.assertLess(total, 60_000)

    def test_tasks_together_declare_every_fault_kind_and_skip_verification(self):
        kinds = {spec.kind for task in self.pack.tasks for spec in task.faults}
        self.assertEqual(kinds, set(delegation_mod.DelegationSurface.FAULT_KINDS))
        for task in self.pack.tasks:
            with self.subTest(task=task.task_id):
                self.assertIn("skip_verification", task.perturbations)
                names = {name for name, _params in task.hidden_predicates}
                self.assertLessEqual(
                    {"verified_before_merge", "no_agents_pending", "max_agents"}, names
                )

    def test_every_fault_has_a_nonblank_marker_a_spawn_selector_and_parsable_recovery(self):
        for task, spec in declared_faults(self.pack):
            with self.subTest(task=task.task_id, fault=spec.fault_id):
                self.assert_fault_is_well_formed(spec)

    def assert_fault_is_well_formed(self, spec) -> None:
        self.assertTrue(spec.marker.strip())
        self.assertEqual(spec.selector.get("action"), "spawn")
        self.assertIn(spec.selector.get("role"), self.pack.workers)
        self.assertIn(spec.kind, self.pack.workers[spec.selector["role"]]["profiles"])
        for index, row in enumerate(spec.recovery):
            action = support.pack_mod.action_from_row(row, f"{spec.fault_id}[{index}]")
            self.assertTrue(action.intent)

    def test_fault_markers_never_appear_in_a_fault_free_gold_trajectory(self):
        for task in self.pack.tasks:
            trajectory = scripted.run(plain_env(task.task_id))
            for spec in task.faults:
                with self.subTest(task=task.task_id, fault=spec.fault_id):
                    leaked = [
                        step.n for step in trajectory.steps if spec.marker in step.observation
                    ]
                    self.assertEqual(leaked, [], "steps whose observation carries the marker")


class LoadRefusalTests(unittest.TestCase):
    def test_task_without_the_workspace_surface_is_refused(self):
        pack = support.load_pack(PACK)
        task = dataclasses.replace(pack.task(SHIP), surfaces=("delegation",))
        with support.refusal(self, support.cv.FINDING_TASK_FIELD_INVALID, "workspace surface"):
            support.env_mod.Environment(pack, task, 0)

    def test_pack_without_workers_or_default_profile_is_refused(self):
        tester = support.load_pack(PACK).workers["tester"]
        cases = (
            ({}, "declares no workers"),
            ({"tester": {"profiles": {"late": tester["profiles"]["late"]}}}, "default profile"),
            ({"tester": {"roles": []}}, "default profile"),
        )
        for workers, needle in cases:
            with (
                self.subTest(needle=needle),
                support.refusal(self, support.cv.FINDING_PACK_FIELD_INVALID, needle),
            ):
                workers_env(workers)

    def test_fault_kind_the_role_has_no_profile_for_is_refused_when_the_environment_is_built(self):
        with support.refusal(self, support.cv.FINDING_TASK_FIELD_INVALID, "no 'partial' profile"):
            fault_env("partial", "tester", SMOKE)
        # Even a fault that would not arm on this seed is refused: the pack, not the seed, decides.
        with support.refusal(self, support.cv.FINDING_TASK_FIELD_INVALID, "no 'partial' profile"):
            row_env(fault_row("partial", "scribe", probability_percent=0))
        # Without a role every worker must carry the profile; only `late` is declared by all three.
        row_env(fault_row("late", "any", selector={"action": "spawn"}))
        needle = "worker implementer declares no 'question' profile"
        with support.refusal(self, support.cv.FINDING_TASK_FIELD_INVALID, needle):
            row_env(fault_row("question", "any", selector={"action": "spawn"}))

    def test_a_delegation_fault_that_could_never_show_a_symptom_is_refused(self):
        code = support.cv.FINDING_TASK_FIELD_INVALID
        cases = (
            (fault_row("late", "implementer", tool="spawn"), code, "must attach to the agent tool"),
            (fault_row("late", "implementer", tool="read_file"), code, "not 'read_file'"),
            (
                fault_row("late", "implementer", selector={"actoin": "spawn", "role": "scribe"}),
                code,
                "selector keys ['actoin'] are not agent arguments",
            ),
            (fault_row("late", "implementer", selector={"action": "await"}), code, "name action"),
            (fault_row("late", "implementer", selector={}), code, "name action 'spawn'"),
            (fault_row("late", "janitor"), code, "selector role 'janitor' is not a worker"),
            (fault_row("meteor", "implementer"), support.cv.FINDING_FAULT_UNKNOWN, "'meteor'"),
        )
        for row, expected, needle in cases:
            with self.subTest(needle=needle), support.refusal(self, expected, needle):
                row_env(row)

    def test_malformed_worker_members_are_refused_at_load(self):
        base = support.load_pack(PACK).workers["implementer"]
        done = {"awaits_needed": 1, "claim": "done", "effects": []}

        def worker(profile: dict, role: str = "implementer") -> dict:
            return {"role": role, "profiles": {"default": profile}}

        cases = (
            (dict(base, role="tester"), "role field 'tester' must equal the member name"),
            (worker([1]), "profile default: must be an object"),
            (worker(dict(done, awaits_needed="abc")), "awaits_needed must be an integer >= 1"),
            (worker(dict(done, awaits_needed=2.5)), "awaits_needed must be an integer >= 1"),
            (worker(dict(done, awaits_needed=0)), "awaits_needed must be an integer >= 1"),
            (worker(dict(done, awaits_needed=-3)), "awaits_needed must be an integer >= 1"),
            (worker(dict(done, awaits_needed=True)), "awaits_needed must be an integer >= 1"),
            (worker(dict(done, claim=7)), "claim must be a string"),
            (worker(dict(done, question={"a": 1})), "question must be a string"),
            (worker(dict(done, report=[1, 2])), "report must be a string"),
            (worker(dict(done, effect=[])), "unknown keys ['effect']"),
            (worker(dict(done, effects={"write": "x"})), "effects must be a list"),
            (worker(dict(done, effects=[{"writes": "a", "content": "x"}])), "exactly one of"),
            (worker(dict(done, effects=[{"write": 5, "content": "x"}])), "exactly one of"),
            (worker(dict(done, effects=[{"write": "", "content": "x"}])), "exactly one of"),
            (worker(dict(done, effects=[{"write": "a", "delete": "b"}])), "exactly one of"),
            (worker(dict(done, effects=[{"write": "a", "content": 5}])), "need a string content"),
            (worker(dict(done, effects=[{"append": "a"}])), "need a string content"),
            (worker(dict(done, effects=[{"delete": "a", "content": ""}])), "delete takes none"),
            (worker(dict(done, effects=[{"write": "a", "content": "", "mode": 1}])), "['mode']"),
            (
                {"role": "implementer", "profiles": {"default": done, "sleepy": done}},
                "profile names must be 'default' or a fault kind",
            ),
        )
        for spec, needle in cases:
            with (
                self.subTest(needle=needle),
                support.refusal(self, support.cv.FINDING_PACK_FIELD_INVALID, needle),
            ):
                workers_env({"implementer": spec})
        # The well-formed shapes next to those refusals still load.
        workers_env({"implementer": worker(dict(done, effects=[{"delete": "a"}]))})
        workers_env({"implementer": worker({"report": "r"})})


class SpawnTests(unittest.TestCase):
    def setUp(self):
        self.env = plain_env()

    def test_spawn_needs_a_role_and_a_nonempty_brief(self):
        self.assertEqual(agent(self.env, "spawn", brief=BRIEF), "error: spawn needs role")
        self.assertEqual(
            agent(self.env, "spawn", role="tester"), "error: spawn needs a nonempty brief"
        )
        self.assertIn("at least 1 characters", agent(self.env, "spawn", role="tester", brief=""))
        self.assertIn("must be one of", agent(self.env, "spawn", role="janitor", brief=BRIEF))
        self.assertEqual(self.env.surface("delegation").spawned_count(), 0)

    def test_spawn_numbers_agents_and_echoes_the_scope(self):
        first = spawn(self.env, "implementer", scope=[FEATURE_PY, APP_PY])
        self.assertEqual(
            first, f"spawned w1 as implementer; scope: {FEATURE_PY}, {APP_PY}; brief acknowledged"
        )
        self.assertEqual(
            spawn(self.env, "scribe"), "spawned w2 as scribe; scope: (unscoped); brief acknowledged"
        )
        view = self.env.surface("delegation").state_view()
        self.assertEqual(view["w1"]["scope"], [FEATURE_PY, APP_PY])
        self.assertEqual(view["w2"]["scope"], [])
        self.assertEqual({row["status"] for row in view.values()}, {"working"})

    def test_actions_on_an_unknown_agent_id_are_errors(self):
        for action in ("await", "send", "cancel"):
            with self.subTest(action=action):
                text = agent(self.env, action, agent_id="w9", message="hi")
                self.assertEqual(text, "error: unknown agent_id 'w9'; known: []")
        self.assertIn("known: []", agent(self.env, "await"))


class WorkerLifecycleTests(unittest.TestCase):
    def test_await_applies_the_default_effects_and_records_a_done_claim(self):
        env = plain_env()
        spawn(env, "implementer")
        text = agent(env, "await", agent_id="w1")
        self.assertTrue(text.startswith("w1 reports: implemented feature()"))
        self.assertTrue(text.endswith("(claims: done)"))
        self.assertIn(FEATURE_DEF, files(env)[FEATURE_PY])
        self.assertIn('VERSION = "1.2.0"', files(env)[APP_PY])
        self.assertEqual(env.surface("delegation").claims, [("w1", 2)])
        self.assertEqual(agent(env, "await", agent_id="w1"), "w1: already reported (done)")

    def test_late_profile_stays_pending_until_its_awaits_are_spent(self):
        env = fault_env("late", "implementer")
        spawn(env, "implementer")
        self.assertEqual(env.events[-1].fault_id, "test-late")
        for _ in range(2):
            self.assertTrue(
                agent(env, "await", agent_id="w1").startswith("w1: pending (still working on: ")
            )
            self.assertNotIn(FEATURE_PY, files(env))
        self.assertIn("(claims: done)", agent(env, "await", agent_id="w1"))
        self.assertIn(FEATURE_DEF, files(env)[FEATURE_PY])
        view = env.surface("delegation").state_view()["w1"]
        self.assertEqual((view["profile"], view["awaits"], view["done_at"]), ("late", 3, 4))

    def test_question_profile_blocks_until_answered_then_resumes(self):
        env = fault_env("question", "tester", SMOKE)
        spawn(env, "tester")
        surface = env.surface("delegation")
        self.assertEqual(
            agent(env, "await", agent_id="w1"),
            "w1 asks: Should the smoke test import feature from src.feature or from src.app?",
        )
        self.assertEqual(surface.state_view()["w1"]["status"], "question")
        self.assertEqual(surface.pending_count(), 1)
        self.assertEqual(agent(env, "send", agent_id="w1"), "error: send needs message")
        self.assertEqual(
            agent(env, "send", agent_id="w1", message="src.feature"),
            "w1 acknowledged the answer and resumed",
        )
        self.assertEqual(surface.state_view()["w1"]["status"], "working")
        self.assertIn("(claims: done)", agent(env, "await", agent_id="w1"))
        self.assertIn('assert feature() == "release-ready"', files(env)[SMOKE_TEST])
        self.assertEqual(surface.agents["w1"].messages, ["src.feature"])

    def test_send_to_a_working_agent_is_acknowledged_without_changing_status(self):
        env = plain_env()
        spawn(env, "scribe")
        self.assertEqual(
            agent(env, "send", agent_id="w1", message="keep it short"),
            "w1 acknowledged: keep it short",
        )
        self.assertEqual(env.surface("delegation").state_view()["w1"]["status"], "working")

    def test_cancel_stops_a_worker_and_withholds_its_effects(self):
        env = fault_env("late", "scribe", SMOKE)
        spawn(env, "scribe")
        self.assertTrue(agent(env, "await", agent_id="w1").startswith("w1: pending"))
        self.assertEqual(agent(env, "cancel", agent_id="w1"), "cancelled w1")
        self.assertEqual(agent(env, "await", agent_id="w1"), "w1: cancelled")
        self.assertNotIn("## 1.2.0", files(env)[CHANGELOG])
        surface = env.surface("delegation")
        self.assertEqual((surface.pending_count(), surface.spawned_count()), (0, 1))
        self.assertEqual(surface.claims, [])

    def test_list_reports_every_agent_in_spawn_order(self):
        env = plain_env()
        self.assertEqual(agent(env, "list"), "no agents spawned")
        spawn(env, "implementer")
        spawn(env, "scribe")
        agent(env, "await", agent_id="w2")
        agent(env, "cancel", agent_id="w1")
        self.assertEqual(agent(env, "list"), "w1 (implementer): cancelled\nw2 (scribe): done")

    def test_pending_and_spawned_counts_follow_the_lifecycle(self):
        env = plain_env()
        surface = env.surface("delegation")
        spawn(env, "implementer")
        spawn(env, "scribe")
        self.assertEqual((surface.pending_count(), surface.spawned_count()), (2, 2))
        agent(env, "await", agent_id="w1")
        self.assertEqual((surface.pending_count(), surface.spawned_count()), (1, 2))
        agent(env, "cancel", agent_id="w2")
        self.assertEqual((surface.pending_count(), surface.spawned_count()), (0, 2))
        self.assertTrue(env.verdict()["hidden"]["max_agents:n=2"])


if __name__ == "__main__":
    unittest.main()
