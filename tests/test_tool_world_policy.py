#!/usr/bin/env python3
"""The scripted policy: decision bases, captures, and the perturbation variants it plays.

The scripted policy is the only author of a decision basis; every test
runs it on the committed ``counter-workspace`` pack and reads the
trajectory it produces.
"""

from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tool_world_record_support import (
    ADD_SUB,
    DELETE_LOCK,
    SEEDS,
    TRANSIENT,
    action,
    call,
    episode,
    refusal,
    task_variant,
)

# The support module goes first: it puts pipelines/ on sys.path for the imports below.
# isort: split
from tool_world import env as env_mod
from tool_world import vocabulary as cv
from tool_world._contract import OBSERVABLE_BASIS_RE
from tool_world.policies import scripted

GOLD_TOOL_NAMES = [
    "run_tests",
    "run_tests",
    "read_file",
    "read_file",
    "edit_file",
    "run_tests",
    cv.TOOL_REPORT,
]


class DecisionBasis(unittest.TestCase):
    def test_a_basis_is_prefix_colon_intent_and_cites_observable_evidence(self):
        basis = scripted.decision_basis("Observation", "the tool output showed one lock")
        self.assertEqual(basis, "Observation: the tool output showed one lock")
        self.assertRegex(basis, OBSERVABLE_BASIS_RE)
        longest = "read " + "x" * (cv.MAX_DECISION_BASIS_CHARS - len("Plan: read "))
        self.assertEqual(len(scripted.decision_basis("Plan", longest)), cv.MAX_DECISION_BASIS_CHARS)

    def test_the_intent_itself_must_cite_evidence_because_every_prefix_is_a_basis_word(self):
        for prefix in cv.DB_PREFIXES:
            with self.subTest(prefix=prefix):
                self.assertRegex(f"{prefix}: ", OBSERVABLE_BASIS_RE)
                with refusal(self, cv.FINDING_DECISION_BASIS_INVALID, "no observable evidence"):
                    scripted.decision_basis(prefix, "just do it now")

    def test_refusals(self):
        cases = (
            (
                "Plan",
                "read " + "x" * cv.MAX_DECISION_BASIS_CHARS,
                f"exceeds {cv.MAX_DECISION_BASIS_CHARS} chars",
            ),
            ("Guess", "read the file", "unknown basis prefix 'Guess'"),
        )
        for prefix, intent, needle in cases:
            with (
                self.subTest(needle=needle),
                refusal(self, cv.FINDING_DECISION_BASIS_INVALID, needle),
            ):
                scripted.decision_basis(prefix, intent)

    def test_a_prefix_added_to_the_vocabulary_still_needs_observable_evidence(self):
        with mock.patch.object(cv, "DB_PREFIXES", (*cv.DB_PREFIXES, "Note")):
            self.assertEqual(
                scripted.decision_basis("Note", "read the file"), "Note: read the file"
            )
            with refusal(self, cv.FINDING_DECISION_BASIS_INVALID, "cites no observable evidence"):
                scripted.decision_basis("Note", "just do it now")


class Captures(unittest.TestCase):
    def test_substitute_replaces_capture_leaves_anywhere_in_the_arguments(self):
        value = {
            "a": {"$capture": "x"},
            "b": [{"$capture": "x"}, 1],
            "c": {"$capture": "x", "k": 1},
        }
        self.assertEqual(
            scripted.substitute(value, {"x": "v"}),
            {"a": "v", "b": ["v", 1], "c": {"$capture": "x", "k": 1}},
        )
        self.assertEqual(scripted.substitute("plain", {}), "plain")
        with refusal(self, cv.FINDING_CAPTURE_FAILED, "capture 'nope' was never taken"):
            scripted.substitute({"path": {"$capture": "nope"}}, {"x": "v"})

    def test_captured_observation_text_flows_into_later_calls_and_the_event_log(self):
        gold = (
            action(
                "search for the pid marker so the lock path is read from the tool output",
                call("search", pattern="pid="),
                {"lock": r"^1 matches:\n(\S+):1: pid="},
            ),
            action(
                "the search result named one lock file; read the captured path",
                call("read_file", path={"$capture": "lock"}),
            ),
            action(
                "the read showed a stale pid; report the result",
                call(cv.TOOL_REPORT, value="stale lock inspected"),
            ),
        )
        env, trajectory, record = episode(DELETE_LOCK, gold=gold, faults=())
        self.assertEqual(trajectory.steps[1].tool_call, call("read_file", path="locks/stale.lock"))
        self.assertEqual(env.events[1].tool_call["args"], {"path": "locks/stale.lock"})
        self.assertTrue(trajectory.steps[1].observation.startswith("locks/stale.lock ("))
        self.assertEqual(
            record["training_view"]["steps"][1]["tool_call"],
            call("read_file", path="locks/stale.lock"),
        )

    def test_a_capture_that_finds_nothing_or_was_never_taken_is_refused(self):
        search = call("search", pattern="pid=")
        read = call("read_file", path={"$capture": "lock"})
        cases = (
            ({"lock": r"nothing-here-(\d+)"}, read, "found nothing in the observation"),
            ({"lock": r"pid="}, read, "found nothing in the observation"),
            ({}, read, "capture 'lock' was never taken"),
        )
        for captures, second, needle in cases:
            gold = (
                action("search for the pid marker in the files", search, captures),
                action("read the file the search found", second),
            )
            pack, task = task_variant(DELETE_LOCK, gold=gold, faults=())
            env = env_mod.Environment(pack, task, 0)
            with self.subTest(needle=needle), refusal(self, cv.FINDING_CAPTURE_FAILED, needle):
                scripted.run(env)


class Perturbations(unittest.TestCase):
    def test_gold_recovers_every_fault_under_every_seed(self):
        for seed in SEEDS:
            with self.subTest(seed=seed):
                env, trajectory, record = episode(ADD_SUB, seed)
                self.assertEqual(len(trajectory.steps), 7)
                self.assertEqual(trajectory.faults_recovered, 2)
                self.assertIs(env.verdict()["success"], True)
                self.assertEqual(env.fault_engine.fired, ("transient-tests", "truncated-read"))
                self.assertEqual(record["curation"]["decision"], cv.DECISION_ACCEPT)
                names = [step.tool_call["name"] for step in trajectory.steps]
                self.assertEqual(names, GOLD_TOOL_NAMES)
                fault_ids = [step.fault_id for step in trajectory.steps][:3]
                self.assertEqual(fault_ids, ["transient-tests", None, "truncated-read"])

    def test_every_recovery_step_cites_the_observation_it_recovers_from(self):
        for seed in SEEDS:
            with self.subTest(seed=seed):
                _env, trajectory, _record = episode(ADD_SUB, seed)
                self.assertEqual(
                    trajectory.steps[1].decision_basis,
                    f"Observation: the observation reported {TRANSIENT!r}; "
                    "retry the interrupted tool call",
                )
                self.assertTrue(
                    trajectory.steps[3].decision_basis.startswith(
                        "Observation: the read was truncated"
                    )
                )
                self.assertEqual(
                    trajectory.steps[3].tool_call,
                    call("read_file", path="src/counter.py", offset=0, limit=4000),
                )
                for step in trajectory.steps:
                    self.assertRegex(step.decision_basis, OBSERVABLE_BASIS_RE)
                    self.assertLessEqual(len(step.decision_basis), cv.MAX_DECISION_BASIS_CHARS)

    def test_wrong_arg_type_sends_a_mistyped_first_argument_then_the_gold_plan(self):
        env, trajectory, record = episode(ADD_SUB, variant="wrong_arg_type")
        first = trajectory.steps[0]
        self.assertEqual(first.tool_call, call("run_tests", suite=7))
        self.assertTrue(first.observation.startswith("error: invalid arguments for run_tests"))
        self.assertTrue(
            first.decision_basis.endswith("(first attempt sends the wrong argument type)")
        )
        self.assertEqual(len(trajectory.steps), 8)
        self.assertIs(env.verdict()["success"], True)
        self.assertEqual(record["curation"]["decision"], cv.DECISION_MEASURE)
        self.assertEqual(record["curation"]["reason_codes"], ["tool_world.variant.wrong_arg_type"])
        self.assertEqual(record["training_view"]["meta"]["variant"], "wrong_arg_type")

    def test_wrong_arg_type_needs_a_first_action_with_arguments(self):
        gold = (
            action("list the files so the plan starts from the observed tree", call("list_dir")),
        )
        pack, task = task_variant(ADD_SUB, gold=gold, perturbations=("wrong_arg_type",), faults=())
        env = env_mod.Environment(pack, task, 0)
        with refusal(self, cv.FINDING_TASK_FIELD_INVALID, "needs an action with arguments"):
            scripted.run(env, "wrong_arg_type")

    def test_skip_verification_drops_the_verification_actions(self):
        _env, trajectory, _record = episode(
            ADD_SUB, variant="skip_verification", perturbations=("skip_verification",), faults=()
        )
        names = [step.tool_call["name"] for step in trajectory.steps]
        self.assertEqual(names, ["run_tests", "read_file", "edit_file", cv.TOOL_REPORT])

    def test_skip_confirmation_drops_the_confirmation_and_the_environment_fails_it(self):
        for seed in SEEDS:
            with self.subTest(seed=seed):
                env, trajectory, record = episode(DELETE_LOCK, seed, "skip_confirmation")
                names = [step.tool_call["name"] for step in trajectory.steps]
                self.assertNotIn(cv.TOOL_CONFIRM, names)
                self.assertIn("delete_file", names)
                self.assertEqual(env.unconfirmed_irreversible, 1)
                self.assertIs(env.verdict()["success"], False)
                self.assertIs(record["training_view"]["reward"]["success"], False)

    def test_give_up_stops_at_the_first_fault_with_a_report(self):
        for seed in SEEDS:
            with self.subTest(seed=seed):
                env, trajectory, _record = episode(ADD_SUB, seed, "give_up_on_fault")
                self.assertEqual(
                    [step.tool_call["name"] for step in trajectory.steps],
                    ["run_tests", cv.TOOL_REPORT],
                )
                self.assertTrue(trajectory.gave_up)
                self.assertEqual(trajectory.faults_recovered, 0)
                self.assertEqual(
                    trajectory.steps[1].decision_basis,
                    f"Observation: the tool call failed with {TRANSIENT!r}; stop here",
                )
                self.assertTrue(
                    trajectory.steps[1].tool_call["args"]["value"].startswith("giving up")
                )
                self.assertIs(env.verdict()["success"], False)

    def test_give_up_without_budget_for_the_report(self):
        env, trajectory, record = episode(ADD_SUB, variant="give_up_on_fault", max_steps=1)
        self.assertEqual(len(trajectory.steps), 1)
        self.assertTrue(trajectory.gave_up)
        self.assertTrue(env.done)
        self.assertEqual(
            record["training_view"]["outcome"],
            f"Failed: {env.task.title}; gave up after the first fault instead of recovering, "
            "so the goal failed",
        )

    def test_an_undeclared_variant_is_refused(self):
        pack, task = task_variant(ADD_SUB)
        with refusal(self, cv.FINDING_TASK_FIELD_INVALID, "does not declare perturbation"):
            scripted.run(env_mod.Environment(pack, task, 0), "skip_confirmation")

    def test_the_budget_ends_the_plan_and_the_environment_fails_it(self):
        env, trajectory, record = episode(ADD_SUB, max_steps=3, faults=())
        self.assertEqual(len(trajectory.steps), 3)
        self.assertTrue(env.done)
        self.assertIs(record["training_view"]["reward"]["success"], False)
        self.assertEqual(
            record["training_view"]["outcome"], f"Failed: {env.task.title}; a goal predicate failed"
        )

    def test_policy_sha256_is_the_digest_of_the_policy_source(self):
        digest = hashlib.sha256(Path(scripted.__file__).read_bytes()).hexdigest()
        self.assertEqual(scripted.policy_sha256(), digest)


if __name__ == "__main__":
    unittest.main()
