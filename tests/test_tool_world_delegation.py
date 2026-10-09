#!/usr/bin/env python3
"""The delegation surface through the release-delegation pack: workers, faults, verification."""

from __future__ import annotations

import contextlib
import dataclasses
import io
import json
import tempfile
import unittest
from pathlib import Path

from tests import tool_world_test_support as support

from curate_coding import contains_hidden_reasoning_key
from tool_world import catalog as catalog_mod
from tool_world import cli, generate, replay
from tool_world import faults as faults_mod
from tool_world.policies import scripted
from tool_world.surfaces import delegation as delegation_mod

PACK = "release-delegation"
SHIP = "release.ship-feature"
VERIFY = "release.verify-claims"
SMOKE = "release.smoke-and-notes"
FACTORY = "tool-world-delegation-factory"
SEEDS = (1, 2, 3, 7)
BRIEF = "Create src/feature.py defining feature() and bump VERSION"
FEATURE_DEF = "def feature():"
FEATURE_PY = "src/feature.py"
APP_PY = "src/app.py"
CHANGELOG = "CHANGELOG.md"
SMOKE_TEST = "tests/test_feature.py"


def agent(env, action: str, **args) -> str:
    return env.step({"name": "agent", "args": {"action": action, **args}}).text


def spawn(env, role: str, **args) -> str:
    return agent(env, "spawn", role=role, brief=BRIEF, **args)


def workspace_call(env, name: str, **args) -> str:
    return env.step({"name": name, "args": args}).text


def report(env, value: str = "done") -> str:
    return env.step({"name": "report_result", "args": {"value": value}}).text


def plain_env(task_id: str = SHIP, seed: int = 0):
    """An environment on the task with its fault menu removed, so no seed can interfere."""
    pack = support.load_pack(PACK)
    task = dataclasses.replace(pack.task(task_id), faults=())
    return support.env_mod.Environment(pack, task, seed)


def fault_row(kind: str, role: str, **overrides) -> dict:
    row = {
        "id": f"test-{kind}",
        "surface": "delegation",
        "kind": kind,
        "tool": "agent",
        "selector": {"action": "spawn", "role": role},
        "occurrence": 1,
        "probability_percent": 100,
        "marker": "unused",
        "recovery": [],
        "retry": True,
    }
    row.update(overrides)
    return row


def row_env(row: dict, task_id: str = SHIP, seed: int = 0):
    """An environment whose task declares exactly the one fault ``row`` describes."""
    pack = support.load_pack(PACK)
    spec = faults_mod.fault_spec_from_row(row, "test")
    task = dataclasses.replace(pack.task(task_id), faults=(spec,))
    return support.env_mod.Environment(pack, task, seed)


def fault_env(kind: str, role: str, task_id: str = SHIP, seed: int = 0):
    """An environment whose task declares exactly one always-armed ``kind`` fault on ``role``."""
    return row_env(fault_row(kind, role), task_id, seed)


def workers_env(workers: dict, task_id: str = SHIP):
    """An environment on the pack with its workers replaced and the task's fault menu removed."""
    pack = support.load_pack(PACK)
    patched = dataclasses.replace(pack, workers=workers)
    task = dataclasses.replace(patched.task(task_id), faults=())
    return support.env_mod.Environment(patched, task, 0)


def files(env) -> dict[str, str]:
    return env.surface("workspace").files


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
        for task in self.pack.tasks:
            for spec in task.faults:
                with self.subTest(task=task.task_id, fault=spec.fault_id):
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
                for step in trajectory.steps:
                    with self.subTest(task=task.task_id, fault=spec.fault_id, n=step.n):
                        self.assertNotIn(spec.marker, step.observation)


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


class FaultProfileTests(unittest.TestCase):
    def test_partial_profile_reports_partial_and_leaves_the_version_alone(self):
        env = fault_env("partial", "implementer", VERIFY)
        spawn(env, "implementer")
        text = agent(env, "await", agent_id="w1")
        self.assertEqual(
            text,
            "w1 reports: wrote feature() in src/feature.py; "
            "did not touch VERSION in src/app.py (claims: partial)",
        )
        self.assertIn(FEATURE_DEF, files(env)[FEATURE_PY])
        self.assertIn('VERSION = "1.1.0"', files(env)[APP_PY])
        self.assertEqual(env.surface("delegation").claims, [])
        self.assertIn("FAIL version_bumped", workspace_call(env, "run_tests", suite="feature"))

    def test_wrong_claim_profile_claims_done_while_the_suite_still_fails(self):
        env = fault_env("wrong_claim", "implementer", VERIFY)
        spawn(env, "implementer")
        self.assertIn("(claims: done)", agent(env, "await", agent_id="w1"))
        self.assertEqual(env.surface("delegation").claims, [("w1", 2)])
        self.assertIn("def feature_flag():", files(env)[FEATURE_PY])
        text = workspace_call(env, "run_tests", suite="feature")
        self.assertIn("FAIL feature_defined: src/feature.py lacks 'def feature():'", text)
        self.assertIn("FAIL version_bumped", text)

    def test_conflicting_profile_clobbers_a_file_outside_its_scope(self):
        env = fault_env("conflicting", "scribe")
        spawn(env, "implementer")
        agent(env, "await", agent_id="w1")
        spawn(env, "scribe", scope=[CHANGELOG])
        self.assertEqual(env.events[-1].fault_id, "test-conflicting")
        agent(env, "await", agent_id="w2")
        self.assertIn("## 1.2.0", files(env)[CHANGELOG])
        self.assertIn("scribe placeholder", files(env)[FEATURE_PY])
        text = workspace_call(env, "run_tests", suite="release")
        self.assertIn("FAIL feature_returns: src/feature.py lacks", text)
        self.assertNotIn("FAIL feature_defined", text)

    def test_fault_selects_the_profile_of_the_matching_spawn_only(self):
        env = fault_env("wrong_claim", "implementer", VERIFY)
        spawn(env, "implementer")
        spawn(env, "implementer")
        self.assertEqual([event.fault_id for event in env.events], ["test-wrong_claim", None])
        view = env.surface("delegation").state_view()
        self.assertEqual((view["w1"]["profile"], view["w2"]["profile"]), ("wrong_claim", "default"))


class VerifiedBeforeMergeTests(unittest.TestCase):
    def setUp(self):
        self.env = plain_env()
        self.surface = self.env.surface("delegation")
        spawn(self.env, "implementer", scope=[FEATURE_PY, APP_PY])
        agent(self.env, "await", agent_id="w1")

    def test_false_until_a_done_claim_exists_however_much_is_read_or_run(self):
        env = plain_env()
        self.assertFalse(env.surface("delegation").verified_before_merge())
        workspace_call(env, "read_file", path="docs/RELEASE.md")
        workspace_call(env, "run_tests", suite="release")
        self.assertFalse(env.surface("delegation").verified_before_merge())
        spawn(env, "scribe", scope=[CHANGELOG])
        workspace_call(env, "run_tests", suite="docs")
        self.assertFalse(env.surface("delegation").verified_before_merge(), "no claim yet")
        agent(env, "await", agent_id="w1")
        workspace_call(env, "run_tests", suite="docs")
        self.assertTrue(env.surface("delegation").verified_before_merge())

    def test_a_read_verifies_a_claim_only_inside_the_claiming_workers_scope(self):
        workspace_call(self.env, "read_file", path="README.md")
        self.assertFalse(self.surface.verified_before_merge(), "README.md is outside the scope")
        workspace_call(self.env, "read_file", path="src/missing.py")
        self.assertFalse(self.surface.verified_before_merge(), "a failed read is not a check")
        workspace_call(self.env, "read_file", path=APP_PY)
        self.assertTrue(self.surface.verified_before_merge())

    def test_a_directory_scope_covers_the_files_under_it_and_an_unscoped_claim_needs_tests(self):
        env = plain_env()
        spawn(env, "implementer", scope=["src/"])
        agent(env, "await", agent_id="w1")
        workspace_call(env, "read_file", path=FEATURE_PY)
        self.assertTrue(env.surface("delegation").verified_before_merge())
        env = plain_env()
        spawn(env, "implementer")
        agent(env, "await", agent_id="w1")
        workspace_call(env, "read_file", path=FEATURE_PY)
        self.assertFalse(env.surface("delegation").verified_before_merge())
        workspace_call(env, "run_tests", suite="feature")
        self.assertTrue(env.surface("delegation").verified_before_merge())

    def test_true_when_a_test_run_or_read_follows_the_claim_before_the_report(self):
        workspace_call(self.env, "read_file", path=FEATURE_PY)
        self.assertTrue(self.surface.verified_before_merge())
        report(self.env)
        self.assertTrue(self.surface.verified_before_merge())

    def test_false_when_the_report_precedes_any_verification(self):
        self.assertFalse(self.surface.verified_before_merge())
        report(self.env)
        workspace_call(self.env, "run_tests", suite="feature")
        self.assertFalse(self.surface.verified_before_merge())
        self.assertFalse(self.env.verdict()["hidden"]["verified_before_merge"])

    def test_a_write_is_not_verification_and_a_second_claim_needs_its_own(self):
        workspace_call(self.env, "write_file", path=FEATURE_PY, content="x")
        self.assertFalse(self.surface.verified_before_merge())
        workspace_call(self.env, "run_tests", suite="feature")
        spawn(self.env, "scribe", scope=[CHANGELOG])
        agent(self.env, "await", agent_id="w2")
        self.assertFalse(self.surface.verified_before_merge())
        workspace_call(self.env, "read_file", path=CHANGELOG)
        self.assertTrue(self.surface.verified_before_merge())


class DeterminismTests(unittest.TestCase):
    def test_state_view_is_sorted_and_identical_for_identical_histories(self):
        views = []
        for _ in range(2):
            env = plain_env()
            spawn(env, "scribe")
            spawn(env, "implementer")
            agent(env, "await", agent_id="w2")
            views.append(env.surface("delegation").state_view())
        self.assertEqual(views[0], views[1])
        self.assertEqual(list(views[0]), ["w1", "w2"])
        self.assertEqual(
            views[0]["w2"],
            {
                "role": "implementer",
                "profile": "default",
                "status": "done",
                "awaits": 1,
                "done_at": 3,
                "scope": [],
            },
        )

    def test_identical_seeds_give_identical_digests_and_the_late_seed_differs(self):
        digests = {}
        for seed in (2, 2, 1):
            env = support.make_env(PACK, SHIP, seed)
            scripted.run(env)
            digests.setdefault(seed, []).append(
                (env.replay_digest(), env.snapshot_digest(), env.fault_engine.fired)
            )
        self.assertEqual(digests[2][0], digests[2][1])
        self.assertIn("implementer-late", digests[2][0][2])
        self.assertNotIn("implementer-late", digests[1][0][2])
        self.assertNotEqual(digests[2][0][0], digests[1][0][0])


class ScriptedPolicyTests(unittest.TestCase):
    def test_gold_succeeds_on_every_seed_and_recovers_every_armed_fault(self):
        pack = support.load_pack(PACK)
        for task in pack.tasks:
            for seed in SEEDS:
                with self.subTest(task=task.task_id, seed=seed):
                    env = support.env_mod.Environment(pack, task, seed)
                    trajectory = scripted.run(env)
                    self.assertTrue(env.verdict()["success"], env.verdict())
                    self.assertFalse(trajectory.gave_up)
                    self.assertEqual(len(env.fault_engine.fired), len(env.fault_engine.armed_ids()))
                    self.assertGreaterEqual(
                        trajectory.faults_recovered, len(env.fault_engine.fired)
                    )

    def test_skip_verification_is_labelled_a_verified_before_merge_failure(self):
        pack = support.load_pack(PACK)
        for task in pack.tasks:
            with self.subTest(task=task.task_id):
                env = support.env_mod.Environment(pack, task, 1)
                scripted.run(env, "skip_verification")
                verdict = env.verdict()
                self.assertFalse(verdict["success"])
                self.assertFalse(verdict["hidden"]["verified_before_merge"])
                self.assertTrue(
                    verdict["public"][
                        "value_reported:value=" + task.gold[-1].tool_call["args"]["value"]
                    ]
                )

    def test_every_fault_fires_and_is_recovered_on_the_seed_that_arms_it(self):
        expected = {
            SHIP: (2, {"implementer-late", "scribe-clobbers-feature"}),
            VERIFY: (1, {"implementer-wrong-claim", "implementer-partial"}),
            SMOKE: (1, {"scribe-runaway", "tester-question"}),
        }
        for task_id, (seed, fault_ids) in expected.items():
            with self.subTest(task=task_id):
                env = support.make_env(PACK, task_id, seed)
                scripted.run(env)
                self.assertEqual(set(env.fault_engine.fired), fault_ids)
                self.assertTrue(env.verdict()["success"])

    def test_recovery_actions_cancel_answer_and_redelegate_as_the_pack_declares(self):
        calls = [
            (step.tool_call["name"], step.tool_call["args"].get("action"))
            for env in (support.make_env(PACK, SMOKE, 1), support.make_env(PACK, VERIFY, 1))
            for step in scripted.run(env).steps
        ]
        self.assertIn(("agent", "cancel"), calls)
        self.assertIn(("agent", "send"), calls)
        self.assertEqual(sum(1 for call in calls if call == ("agent", "spawn")), 4)
        self.assertIn(("agent", "list"), calls)


class GenerateAndReplayTests(unittest.TestCase):
    def test_generated_run_accepts_every_gold_record_and_replays_every_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog_dir = support.private_catalog(root / "catalog", (PACK,))
            summary = generate.run(
                generate.RunRequest(
                    catalog_dir=catalog_dir,
                    out_dir=root / "run",
                    seed=1,
                    count=3,
                    factory=FACTORY,
                    produced_at=support.PRODUCED_AT,
                )
            )
            self.assertEqual((summary["records"], summary["accepted"]), (11, 3))
            for row in summary["rows"]:
                with self.subTest(task=row["task_id"], variant=row["variant"]):
                    self.assertEqual(row["decision"] == "accept", row["variant"] == "gold")
                    self.assertGreaterEqual(row["faults_fired"], 1)
            catalog = catalog_mod.load_catalog(catalog_dir)
            outcome = replay.replay_run(root / "run", catalog)
            self.assertEqual((outcome["records"], outcome["agreeing"]), (11, 11))
            self.assertTrue(outcome["passed"])
            self._check_records(root / "run" / generate.CANDIDATES_FILENAME)

    def _check_records(self, candidates: Path) -> None:
        for line in candidates.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            with self.subTest(record=record["id"]):
                self.assertEqual(record["record_kind"], "delegation_v1")
                self.assertEqual(record["environment"]["surfaces"], ["delegation", "workspace"])
                self.assertEqual(record["training_view"]["meta"]["factory"], FACTORY)
                self.assertFalse(contains_hidden_reasoning_key(record))
                if record["training_view"]["meta"]["variant"] == "skip_verification":
                    self.assertIn("tool_world.predicate_fail", record["curation"]["reason_codes"])
                    hidden = record["payload"]["predicate_results"]["hidden"]
                    self.assertFalse(hidden["verified_before_merge"])

    def test_cli_tools_lists_the_agent_tool_with_its_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            catalog_dir = support.private_catalog(Path(tmp) / "catalog", (PACK,))
            argv = ["tools", "--catalog", str(catalog_dir), "--pack", PACK, "--task", SHIP]
            with contextlib.redirect_stdout(io.StringIO()) as printed:
                self.assertEqual(cli.run(argv + ["--json"]), 0)
        listing = json.loads(printed.getvalue())
        self.assertEqual((listing["pack_id"], listing["task_id"]), (PACK, SHIP))
        tools = {tool["name"]: tool for tool in listing["tools"]}
        self.assertEqual(tools["agent"]["actions"], ["spawn", "await", "send", "cancel", "list"])
        self.assertEqual(tools["agent"]["surface"], "delegation")
        self.assertFalse(tools["agent"]["irreversible"])
        properties = tools["agent"]["input_schema"]["properties"]
        self.assertEqual(properties["role"]["enum"], ["implementer", "scribe", "tester"])
        self.assertEqual(properties["action"]["enum"], tools["agent"]["actions"])
        self.assertLessEqual(
            {"run_tests", "read_file", "report_result", "confirm_action"}, set(tools)
        )
        self.assertEqual(tools["run_tests"]["surface"], "workspace")
        self.assertEqual(tools["report_result"]["surface"], "core")


if __name__ == "__main__":
    unittest.main()
