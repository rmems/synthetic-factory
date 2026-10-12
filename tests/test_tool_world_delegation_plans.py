#!/usr/bin/env python3
"""Delegation fault profiles, verified-before-merge, determinism, gold plans, and replay."""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from tests import tool_world_test_support as support
from tests.tool_world_delegation_support import (
    APP_PY,
    CHANGELOG,
    FACTORY,
    FEATURE_DEF,
    FEATURE_PY,
    PACK,
    SEEDS,
    SHIP,
    SMOKE,
    VERIFY,
    agent,
    fault_env,
    files,
    plain_env,
    report,
    spawn,
    workspace_call,
)

from curate_coding import contains_hidden_reasoning_key
from tool_world import catalog as catalog_mod
from tool_world import cli, generate, replay
from tool_world.policies import scripted


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
