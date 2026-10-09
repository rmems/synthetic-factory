#!/usr/bin/env python3
"""Records, the scripted policy, seeded generation, and fresh replay on the workspace pack.

The record builder is the only writer of a training view, the scripted
policy the only author of a decision basis, and ``replay`` the oracle that
re-executes a record's own actions; each is exercised through the committed
``counter-workspace`` pack in a private catalog.
"""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tool_world_test_support as support
from tool_world import catalog as catalog_mod
from tool_world import env as env_mod
from tool_world import generate, records, replay
from tool_world import pack as pack_mod
from tool_world import vocabulary as cv
from tool_world._contract import (
    OBSERVABLE_BASIS_RE,
    check_episode,
    contains_hidden_reasoning_key,
    load_strict_json,
    sha256_bytes,
)
from tool_world.policies import scripted

PACK = "counter-workspace"
ADD_SUB = "counter.add-sub"
DELETE_LOCK = "counter.delete-stale-lock"
FACTORY = "tool-world-workspace-factory"
SEEDS = (1, 2, 3, 7)
HEX64 = "0" * 64
RECORD_ID = re.compile(r"^twd-[0-9a-f]{16}-[0-9a-f]{16}-\d+-\d{5}$")
TRANSIENT = "EAGAIN temporary failure"
refusal = support.refusal


def call(name: str, **args) -> dict:
    return {"name": name, "args": args}


def action(intent: str, tool_call: dict, captures: dict | None = None, **flags) -> pack_mod.Action:
    return pack_mod.Action(
        intent=intent,
        tool_call=tool_call,
        captures=captures or {},
        verification=flags.get("verification", False),
        confirmation=flags.get("confirmation", False),
    )


def task_variant(task_id: str, **replace) -> tuple[pack_mod.Pack, pack_mod.Task]:
    pack = support.load_pack(PACK)
    return pack, dataclasses.replace(pack.task(task_id), **replace)


def build(env, trajectory) -> dict:
    run = records.RunContext(HEX64, "twd-run-test", scripted.policy_sha256())
    return records.build_record(env, trajectory, run, 1)


def episode(task_id: str, seed: int = 1, variant: str = cv.VARIANT_GOLD, **replace):
    """Run the scripted policy on one task and assemble its record."""
    pack, task = task_variant(task_id, **replace)
    env = env_mod.Environment(pack, task, seed)
    trajectory = scripted.run(env, variant)
    return env, trajectory, build(env, trajectory)


def gate(view: dict) -> list[str]:
    return check_episode(
        view, "training_view", forbid_hidden_thought=True, enforce_terminal_outcome=True
    )


def read_candidates(run_dir: Path) -> list[dict]:
    lines = (run_dir / generate.CANDIDATES_FILENAME).read_text(encoding="utf-8").splitlines()
    return [load_strict_json(line) for line in lines if line.strip()]


def resign_bytes(run_dir: Path, payload: bytes) -> None:
    """Write raw candidate bytes and keep RUN.json's digest consistent with them."""
    (run_dir / generate.CANDIDATES_FILENAME).write_bytes(payload)
    run_file = run_dir / generate.RUN_FILENAME
    summary = json.loads(run_file.read_text(encoding="utf-8"))
    summary["candidates_sha256"] = sha256_bytes(payload)
    run_file.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def resign_run(run_dir: Path, candidates: list[dict]) -> None:
    """Rewrite the candidates and keep RUN.json's digest consistent with them."""
    payload = "\n".join(json.dumps(record, sort_keys=True) for record in candidates) + "\n"
    resign_bytes(run_dir, payload.encode("utf-8"))


def _set_step(index: int, key: str, value):
    return lambda record: record["training_view"]["steps"][index].__setitem__(key, value)


def _set_in(*path: str):
    def mutate(record: dict, value) -> None:
        target = record
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value

    return lambda value: lambda record: mutate(record, value)


# Rewrites of the trainable projection the design says replay must detect.
TRAINING_VIEW_TAMPERINGS = (
    (
        "training_view tool_call",
        _set_step(1, "tool_call", call("delete_file", path="README.md")),
        "step 2: training_view tool_call differs",
    ),
    (
        "training_view tool_call arguments",
        lambda r: r["training_view"]["steps"][0]["tool_call"]["args"].__setitem__(
            "pattern", "rm -rf /"
        ),
        "step 1: training_view tool_call differs",
    ),
    ("step number", _set_step(0, "n", 9), "step 1: training_view step number differs"),
    ("hidden-reasoning key", _set_step(0, "reasoning", "x"), "hidden-reasoning key"),
    (
        "empty decision basis",
        _set_step(0, "decision_basis", ""),
        "decision_basis must be a non-empty",
    ),
    (
        "decision basis text",
        _set_step(0, "decision_basis", "Plan: just do it now"),
        "the scripted policy replays a different gold trajectory",
    ),
    (
        "outcome text",
        _set_in("training_view", "outcome")("Failed: everything broke"),
        "training_view.outcome differs from the replayed value",
    ),
    ("goal", _set_in("training_view", "goal")("do something else"), "training_view.goal differs"),
    (
        "cost_steps",
        _set_in("training_view", "reward", "cost_steps")(99),
        "reward.cost_steps differs",
    ),
    ("meta seed", _set_in("training_view", "meta", "seed")(5), "training_view.meta.seed differs"),
    (
        "training_view id",
        _set_in("training_view", "id")("twd-other-00001"),
        "training_view.id differs",
    ),
)
# Relabels of who proposed and how the record was curated.
LABEL_TAMPERINGS = (
    ("decision", _set_in("curation", "decision")("measure"), "curation.decision differs"),
    ("reason codes", _set_in("curation", "reason_codes")(["x"]), "curation.reason_codes differs"),
    (
        "tool policy",
        _set_in("solver", "tool_policy")("workspace-skip_verification"),
        "solver.tool_policy differs",
    ),
    ("solver outcome", _set_in("solver", "outcome")("failure"), "solver.outcome differs"),
    ("record id", _set_in("id")("twd-forged-00001"), "id differs from the replayed value"),
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
        _set_in("payload", "task_specification")("x"),
        "payload.task_specification differs",
    ),
    (
        "faults fired",
        _set_in("payload", "execution_evidence", "faults_fired")([]),
        "faults_fired differs",
    ),
    (
        "faults armed",
        _set_in("payload", "execution_evidence", "faults_armed")(["ghost"]),
        "faults_armed differs",
    ),
    (
        "gave up",
        _set_in("payload", "execution_evidence", "gave_up")(True),
        "gave_up or faults_recovered differ from the scripted policy's run",
    ),
    (
        "faults recovered",
        _set_in("payload", "execution_evidence", "faults_recovered")(9),
        "faults_recovered differs",
    ),
    ("payload outcome", _set_in("payload", "outcome")("failure"), "payload.outcome differs"),
    (
        "catalog digest",
        _set_in("environment", "catalog_sha256")(HEX64),
        "environment.catalog_sha256 differs",
    ),
    ("oracle signals", _set_in("oracle", "signals")([]), "oracle.signals differs"),
)


# --- records -----------------------------------------------------------------


class RecordShape(unittest.TestCase):
    def test_a_gold_record_passes_the_episode_gate_and_separates_its_actors(self):
        env, _trajectory, record = episode(ADD_SUB)
        task, pack = env.task, env.pack
        view = record["training_view"]
        self.assertEqual(gate(view), [])
        self.assertFalse(contains_hidden_reasoning_key(record))
        self.assertIs(view["reward"]["success"], True)
        self.assertEqual(view["outcome"], f"Succeeded: {task.title}")
        self.assertEqual(view["reward"], {"success": True, "cost_steps": 7, "faults_recovered": 2})
        self.assertRegex(record["id"], RECORD_ID)
        self.assertEqual(record["id"], view["id"])
        self.assertEqual(
            (record["schema_version"], record["record_kind"], record["family"]),
            (cv.RECORD_SCHEMA_VERSION, "tool_episode_v1", cv.FAMILY),
        )
        self.assertEqual(
            record["task_author"],
            {
                "model": cv.TASK_AUTHOR_MODEL,
                "version": pack.pack_sha256,
                "prompt_hash": f"sha256:{task.spec_sha256}",
                "run_id": "twd-run-test",
            },
        )
        self.assertEqual(
            record["solver"],
            {
                "model": cv.GENERATOR_NAME,
                "version": scripted.policy_sha256(),
                "tool_policy": "workspace-gold",
                "run_id": "twd-run-test",
                "outcome": cv.OUTCOME_SUCCESS,
            },
        )
        self.assertEqual(
            record["oracle"],
            {
                "kind": cv.ORACLE_KIND,
                "status": "validated",
                "repo_commit": pack.pack_sha256,
                "command": (
                    f"python3 pipelines/tool_world_cli.py replay <run_dir> --record {record['id']}"
                ),
                "result_hash": f"sha256:{env.replay_digest()}",
                "certifier": cv.ORACLE_CERTIFIER,
                "signals": ["deterministic_environment", "replay_agreement", "predicate_pass"],
            },
        )
        self.assertEqual(
            record["curation"],
            {
                "pipeline_version": cv.CURATION_PIPELINE_VERSION,
                "decision": "accept",
                "reason_codes": [],
            },
        )
        self.assertEqual(
            record["environment"],
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
            view["meta"],
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
        self.assertEqual(
            record["payload"]["predicate_results"]["hidden"][
                "no_irreversible_without_confirmation"
            ],
            False,
        )

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
        _env, trajectory, record = episode(ADD_SUB, variant="give_up_on_fault")
        self.assertTrue(trajectory.gave_up)
        self.assertEqual(
            record["training_view"]["outcome"],
            "Failed: gave up after the first fault instead of recovering",
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


# --- the scripted policy --------------------------------------------------------


class DecisionBasis(unittest.TestCase):
    def test_a_basis_is_prefix_colon_intent_and_cites_observable_evidence(self):
        basis = scripted.decision_basis("Observation", "the tool output showed one lock")
        self.assertEqual(basis, "Observation: the tool output showed one lock")
        self.assertRegex(basis, OBSERVABLE_BASIS_RE)
        longest = "read " + "x" * (cv.MAX_DECISION_BASIS - len("Plan: read "))
        self.assertEqual(len(scripted.decision_basis("Plan", longest)), cv.MAX_DECISION_BASIS)

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
                "read " + "x" * cv.MAX_DECISION_BASIS,
                f"exceeds {cv.MAX_DECISION_BASIS} chars",
            ),
            ("Guess", "read the file", "unknown basis prefix 'Guess'"),
        )
        for prefix, intent, needle in cases:
            with (
                self.subTest(needle=needle),
                refusal(self, cv.FINDING_DECISION_BASIS_INVALID, needle),
            ):
                scripted.decision_basis(prefix, intent)
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
                self.assertEqual(
                    names,
                    [
                        "run_tests",
                        "run_tests",
                        "read_file",
                        "read_file",
                        "edit_file",
                        "run_tests",
                        cv.TOOL_REPORT,
                    ],
                )
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
                    self.assertLessEqual(len(step.decision_basis), cv.MAX_DECISION_BASIS)
                self.assertEqual(
                    [step.fault_id for step in trajectory.steps][:3],
                    [
                        "transient-tests",
                        None,
                        "truncated-read",
                    ],
                )

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
        self.assertTrue(trajectory.gave_up and env.done)
        self.assertEqual(
            record["training_view"]["outcome"],
            "Failed: gave up after the first fault instead of recovering",
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


# --- generation and replay ------------------------------------------------------


class RunCase(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="tool-world-replay-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.catalog_dir = support.private_catalog(self.root / "catalog", (PACK,))
        self.catalog = catalog_mod.load_catalog(self.catalog_dir)

    def request(self, **overrides) -> generate.RunRequest:
        fields = {
            "catalog_dir": self.catalog_dir,
            "out_dir": self.root / "run",
            "seed": 1,
            "count": 2,
            "factory": FACTORY,
            "variants": "all",
            "produced_at": support.PRODUCED_AT,
        }
        fields.update(overrides)
        return generate.RunRequest(**fields)


class ReplayAgreement(RunCase):
    def setUp(self):
        super().setUp()
        self.run_dir = self.root / "run"
        self.summary = generate.run(self.request())
        self.candidates = read_candidates(self.run_dir)

    def test_a_generated_run_replays_in_full(self):
        report = replay.replay_run(self.run_dir, self.catalog)
        self.assertEqual(report["run_dir"], str(self.run_dir))
        self.assertEqual(report["records"], self.summary["records"])
        self.assertEqual((report["agreeing"], report["passed"]), (report["records"], True))
        for row, record in zip(report["results"], self.candidates, strict=True):
            self.assertEqual(row["id"], record["id"])
            self.assertEqual((row["agreement"], row["mismatches"]), (True, []))
            self.assertEqual(f"sha256:{row['replay_digest']}", record["oracle"]["result_hash"])
            self.assertEqual(row["success"], record["training_view"]["reward"]["success"])

    def test_every_tampering_is_reported_as_a_mismatch(self):
        base = self.candidates[0]

        def flip_predicate(record):
            public = record["payload"]["predicate_results"]["public"]
            key = next(iter(public))
            public[key] = not public[key]

        def flip_success(record):
            record["training_view"]["reward"]["success"] = not record["training_view"]["reward"][
                "success"
            ]

        cases = (
            (
                "observation text",
                lambda r: r["training_view"]["steps"][0].__setitem__("observation", "edited"),
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
                lambda r: r["payload"].__setitem__("final_state_digest", HEX64),
                "final state digest differs",
            ),
            ("predicate results", flip_predicate, "predicate verdicts differ"),
            (
                "result hash",
                lambda r: r["oracle"].__setitem__("result_hash", f"sha256:{HEX64}"),
                "oracle.result_hash differs from the replay digest",
            ),
            ("reward.success", flip_success, "reward.success differs from the replayed verdict"),
            (
                "action arguments",
                lambda r: r["payload"]["actions"][0]["tool_call"].__setitem__(
                    "args", {"nonsense": True}
                ),
                "step 1: observation digest differs",
            ),
            ("dropped step", lambda r: r["training_view"]["steps"].pop(), "training_view has"),
            *TRAINING_VIEW_TAMPERINGS,
            *LABEL_TAMPERINGS,
            *EVIDENCE_TAMPERINGS,
        )
        for label, mutate, needle in cases:
            record = copy.deepcopy(base)
            mutate(record)
            with self.subTest(label=label):
                result = replay.replay_record(record, self.catalog)
                self.assertFalse(result.agreement)
                self.assertEqual(result.record_id, record["id"])
                self.assertTrue(
                    any(needle in item for item in result.mismatches), result.mismatches
                )
                self.assertEqual(result.row()["mismatches"], list(result.mismatches))

    def test_a_consistent_relabel_of_a_perturbed_record_is_caught_by_rerunning_the_policy(self):
        perturbed = next(
            record
            for record in self.candidates
            if record["training_view"]["meta"]["variant"] != cv.VARIANT_GOLD
        )
        relabelled = copy.deepcopy(perturbed)
        success = relabelled["training_view"]["reward"]["success"]
        relabelled["training_view"]["meta"]["variant"] = cv.VARIANT_GOLD
        relabelled["solver"]["tool_policy"] = "workspace-gold"
        relabelled["curation"]["decision"] = cv.DECISION_ACCEPT if success else cv.DECISION_MEASURE
        relabelled["curation"]["reason_codes"] = records.reason_codes(cv.VARIANT_GOLD, success)
        result = replay.replay_record(relabelled, self.catalog)
        self.assertFalse(result.agreement)
        self.assertIn("the scripted policy replays a different gold trajectory", result.mismatches)
        self.assertNotIn("curation.decision differs from the replayed value", result.mismatches)

    def test_a_record_from_another_policy_version_cannot_be_rerun_and_says_so(self):
        record = copy.deepcopy(self.candidates[0])
        record["solver"]["version"] = HEX64
        result = replay.replay_record(record, self.catalog)
        self.assertIn(
            "solver.version is not the loaded scripted policy, so its plan cannot be re-run",
            result.mismatches,
        )
        self.assertIn("id differs from the replayed value", result.mismatches)

    def test_a_record_the_catalog_cannot_bind_is_refused(self):
        base = self.candidates[0]
        cases = (
            (
                "pack digest",
                lambda r: r["environment"].__setitem__("pack_sha256", HEX64),
                cv.FINDING_PACK_SHA_MISMATCH,
                "generated from pack digest",
            ),
            (
                "pack id",
                lambda r: r["environment"].__setitem__("pack_id", "nope"),
                cv.FINDING_PACK_FILE_MISSING,
                "'nope' is not in catalog",
            ),
            (
                "task id",
                lambda r: r["environment"].__setitem__("task_id", "counter.nope"),
                cv.FINDING_TASK_NOT_FOUND,
                "'counter.nope'",
            ),
            (
                "seed",
                lambda r: r["environment"].__setitem__("seed", -1),
                cv.FINDING_SEED_INVALID,
                "seed must lie",
            ),
            (
                "schema version",
                lambda r: r.__setitem__("schema_version", "other"),
                cv.FINDING_RECORD_MALFORMED,
                "schema_version must be",
            ),
            (
                "missing actions",
                lambda r: r["payload"].pop("actions"),
                cv.FINDING_RECORD_MALFORMED,
                "record lacks payload.actions",
            ),
            (
                "missing environment",
                lambda r: r.pop("environment"),
                cv.FINDING_RECORD_MALFORMED,
                "record lacks environment.pack_id",
            ),
            (
                "actions not a list",
                lambda r: r["payload"].__setitem__("actions", {}),
                cv.FINDING_RECORD_MALFORMED,
                "actions and steps must be lists",
            ),
            (
                "action without tool_call",
                lambda r: r["payload"]["actions"].__setitem__(0, {"n": 1}),
                cv.FINDING_RECORD_MALFORMED,
                "actions[0] must carry a tool_call",
            ),
            (
                "too many actions",
                lambda r: r["payload"].__setitem__("actions", r["payload"]["actions"] * 20),
                cv.FINDING_RECORD_MALFORMED,
                "exceed max_steps",
            ),
            (
                "steps not objects",
                lambda r: r["training_view"].__setitem__("steps", ["x"]),
                cv.FINDING_RECORD_MALFORMED,
                "training_view.steps[0] must be an object",
            ),
            (
                "reward not an object",
                lambda r: r["training_view"].__setitem__("reward", "x"),
                cv.FINDING_RECORD_MALFORMED,
                "training_view.reward must be an object",
            ),
            (
                "variant undeclared",
                lambda r: r["training_view"]["meta"].__setitem__("variant", "skip_tests"),
                cv.FINDING_RECORD_MALFORMED,
                "variant 'skip_tests' is neither gold nor a perturbation",
            ),
            (
                "id without a draw",
                lambda r: r.__setitem__("id", "twd-x"),
                cv.FINDING_RECORD_MALFORMED,
                "id must end in the draw number",
            ),
            (
                "gave_up not a bool",
                lambda r: r["payload"]["execution_evidence"].__setitem__("gave_up", "no"),
                cv.FINDING_RECORD_MALFORMED,
                "payload.execution_evidence.gave_up must be bool",
            ),
            (
                "solver version not a string",
                lambda r: r["solver"].__setitem__("version", 7),
                cv.FINDING_RECORD_MALFORMED,
                "solver.version must be str",
            ),
            (
                "missing oracle",
                lambda r: r.pop("oracle"),
                cv.FINDING_RECORD_MALFORMED,
                "record lacks oracle",
            ),
            (
                "curation not an object",
                lambda r: r.__setitem__("curation", []),
                cv.FINDING_RECORD_MALFORMED,
                "curation must be an object",
            ),
        )
        for label, mutate, code, needle in cases:
            record = copy.deepcopy(base)
            mutate(record)
            with self.subTest(label=label), refusal(self, code, needle):
                replay.replay_record(record, self.catalog)
        with refusal(self, cv.FINDING_INPUT_NOT_AN_OBJECT, "record must be an object"):
            replay.replay_record("not a record", self.catalog)

    def test_corrupt_run_files_are_coded_refusals(self):
        original = (self.run_dir / generate.CANDIDATES_FILENAME).read_bytes()
        lines = original.splitlines()
        resign_bytes(self.run_dir, b"\n".join([b"{not json", *lines[1:]]) + b"\n")
        with refusal(self, cv.FINDING_RECORD_MALFORMED, "line 1 is not strict JSON"):
            replay.load_records(self.run_dir)
        resign_bytes(self.run_dir, b"\n".join([b"[]", *lines[1:]]) + b"\n")
        with refusal(self, cv.FINDING_RECORD_MALFORMED, "line 1 is not an object"):
            replay.load_records(self.run_dir)
        resign_bytes(self.run_dir, original + b"\xff")
        with refusal(self, cv.FINDING_RECORD_MALFORMED, "candidates.jsonl is not UTF-8"):
            replay.load_records(self.run_dir)
        resign_bytes(self.run_dir, original)
        run_file = self.run_dir / generate.RUN_FILENAME
        run_file.write_text('{"format": 1, "format": 2}', encoding="utf-8")
        with refusal(self, cv.FINDING_RUN_FILE_INVALID, "RUN.json is not strict JSON"):
            replay.replay_run(self.run_dir, self.catalog)
        run_file.write_text("[]", encoding="utf-8")
        with refusal(self, cv.FINDING_RUN_FILE_INVALID, "RUN.json must be an object"):
            replay.replay_run(self.run_dir, self.catalog)

    def test_run_level_refusals(self):
        candidates = self.run_dir / generate.CANDIDATES_FILENAME
        candidates.write_bytes(candidates.read_bytes() + b" ")
        with refusal(self, cv.FINDING_RUN_SHA_MISMATCH, "do not match RUN.json candidates_sha256"):
            replay.replay_run(self.run_dir, self.catalog)
        (self.run_dir / generate.RUN_FILENAME).unlink()
        with refusal(self, cv.FINDING_RUN_FILE_MISSING, "missing RUN.json"):
            replay.replay_run(self.run_dir, self.catalog)
        candidates.unlink()
        with refusal(self, cv.FINDING_RUN_FILE_MISSING, "missing candidates.jsonl"):
            replay.replay_run(self.run_dir, self.catalog)

    def test_a_tampered_record_fails_only_itself(self):
        tampered = copy.deepcopy(self.candidates)
        tampered[0]["training_view"]["reward"]["success"] = not tampered[0]["training_view"][
            "reward"
        ]["success"]
        resign_run(self.run_dir, tampered)
        report = replay.replay_run(self.run_dir, self.catalog)
        self.assertFalse(report["passed"])
        self.assertEqual(report["agreeing"], report["records"] - 1)
        self.assertFalse(report["results"][0]["agreement"])
        self.assertTrue(all(row["agreement"] for row in report["results"][1:]))


class GenerateRun(RunCase):
    def test_two_runs_with_one_seed_are_byte_identical(self):
        first = generate.run(self.request(out_dir=self.root / "a"))
        second = generate.run(self.request(out_dir=self.root / "b"))
        self.assertEqual(first, second)
        for name in (generate.CANDIDATES_FILENAME, generate.RUN_FILENAME, generate.NOTES_FILENAME):
            with self.subTest(file=name):
                self.assertEqual(
                    (self.root / "a" / name).read_bytes(), (self.root / "b" / name).read_bytes()
                )
        self.assertIn(
            "Run seed 1", (self.root / "a" / generate.NOTES_FILENAME).read_text(encoding="utf-8")
        )

    def test_the_summary_describes_a_candidate_only_run(self):
        summary = generate.run(self.request())
        candidates = (self.root / "run" / generate.CANDIDATES_FILENAME).read_bytes()
        self.assertEqual(
            (
                summary["format"],
                summary["family"],
                summary["generator"],
                summary["generator_version"],
            ),
            (cv.RUN_FORMAT, cv.FAMILY, cv.GENERATOR_NAME, cv.GENERATOR_VERSION),
        )
        self.assertEqual(summary["run_id"], f"twd-run-1-{self.catalog.catalog_sha256[:12]}")
        self.assertEqual(summary["catalog_sha256"], self.catalog.catalog_sha256)
        self.assertEqual(summary["policy_sha256"], scripted.policy_sha256())
        self.assertEqual((summary["seed"], summary["count"], summary["factory"]), (1, 2, FACTORY))
        self.assertEqual(summary["produced_at"], support.PRODUCED_AT)
        self.assertEqual(summary["records"], len(summary["rows"]))
        self.assertEqual(summary["records"], summary["accepted"] + summary["measured"])
        self.assertEqual(summary["candidates_sha256"], sha256_bytes(candidates))
        self.assertEqual(
            (summary["candidate_only"], summary["self_certified_training_ready"]), (True, False)
        )
        self.assertEqual(
            load_strict_json(
                (self.root / "run" / generate.RUN_FILENAME).read_text(encoding="utf-8")
            ),
            summary,
        )
        for row in summary["rows"]:
            self.assertEqual(
                set(row),
                {
                    "id",
                    "task_id",
                    "factory",
                    "variant",
                    "steps",
                    "success",
                    "decision",
                    "faults_fired",
                },
            )

    def test_gold_only_runs_accept_every_record(self):
        summary = generate.run(self.request(variants="gold", count=3))
        self.assertEqual(summary["records"], 3)
        for row in summary["rows"]:
            with self.subTest(task=row["task_id"]):
                self.assertEqual(
                    (row["variant"], row["decision"], row["success"]), ("gold", "accept", True)
                )
        for record in read_candidates(self.root / "run"):
            self.assertEqual(record["training_view"]["meta"]["variant"], "gold")

    def test_one_record_is_reproducible_without_the_batch(self):
        summary = generate.run(self.request())
        first = read_candidates(self.root / "run")[0]
        row = summary["rows"][0]
        pack = self.catalog.pack(PACK)
        draw = generate.Draw(pack, pack.task(row["task_id"]), row["variant"], 1)
        self.assertEqual(first["environment"]["seed"], draw.seed(1))
        run = records.RunContext(
            self.catalog.catalog_sha256, summary["run_id"], summary["policy_sha256"]
        )
        self.assertEqual(generate.generate_record(draw, 1, run), first)
        self.assertNotEqual(draw.seed(1), dataclasses.replace(draw, index=2).seed(1))
        self.assertNotEqual(draw.seed(1), draw.seed(2))

    def test_request_refusals(self):
        cases = (
            ({"seed": "7"}, cv.FINDING_SEED_INVALID),
            ({"seed": True}, cv.FINDING_SEED_INVALID),
            ({"seed": -1}, cv.FINDING_SEED_INVALID),
            ({"count": 0}, cv.FINDING_COUNT_OUT_OF_DOMAIN),
            ({"count": cv.MAX_COUNT + 1}, cv.FINDING_COUNT_OUT_OF_DOMAIN),
            ({"count": cv.MAX_COUNT}, cv.FINDING_COUNT_OUT_OF_DOMAIN),
            ({"variants": "some"}, cv.FINDING_COUNT_OUT_OF_DOMAIN),
            ({"factory": "tool-world-shell-factory"}, cv.FINDING_SURFACE_UNKNOWN),
            ({"produced_at": "yesterday"}, cv.FINDING_PRODUCED_AT_NOT_A_TIMESTAMP),
        )
        for overrides, code in cases:
            with self.subTest(overrides=overrides), refusal(self, code):
                generate.run(self.request(**overrides))
        self.assertFalse((self.root / "run").exists())

    def test_destinations_that_exist_or_alias_the_raw_tree_are_refused(self):
        (self.root / "run").mkdir()
        with refusal(self, cv.FINDING_DESTINATION_EXISTS, "already exists"):
            generate.run(self.request())
        raw = self.root / "outputs" / "raw" / "run"
        with refusal(self, cv.FINDING_DESTINATION_UNDER_RAW, "raw tree"):
            generate.run(self.request(out_dir=raw))
        self.assertFalse(raw.exists())


if __name__ == "__main__":
    unittest.main()
