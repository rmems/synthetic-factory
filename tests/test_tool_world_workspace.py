#!/usr/bin/env python3
"""The workspace surface through the counter-workspace pack: tools, suites, faults, replay."""

import contextlib
import copy
import dataclasses
import io
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
    make_env,
    pack_mod,
    private_catalog,
    refusal,
)

# The support module goes first: it puts pipelines/ on sys.path for the imports below.
# isort: split
from tool_world import cli, generate, records, replay
from tool_world import faults as faults_mod
from tool_world._contract import contains_hidden_reasoning_key, load_strict_json, sha256_bytes
from tool_world.policies import scripted
from tool_world.surfaces import workspace as workspace_mod

PACK = "counter-workspace"
ADD_SUB = "counter.add-sub"
DELETE_LOCK = "counter.delete-stale-lock"
DOCUMENT = "counter.document-timeout"
RENAME = "counter.rename-config-key"
TASKS = (ADD_SUB, DELETE_LOCK, DOCUMENT, RENAME)
FACTORY = "tool-world-workspace-factory"
SEEDS = (1, 2, 3, 7)
COUNTER = "src/counter.py"
LOCK = "locks/stale.lock"
NOTE = "docs/settings.md"
GET_ANCHOR = "    def get(self):"
SUB_METHOD = (
    "    def sub(self, delta):\n        self._value -= int(delta)\n        return self._value\n\n"
    "    def get(self):"
)
NO_CONFIRMATION = "no_irreversible_without_confirmation"
RENAMED_CONFIG_SHA256 = "eab60e54266f6a91d9e7b5f038a26ffcf435980403e599ebc7626932a8c95310"
EAGAIN = "error: EAGAIN temporary failure on"
TRUNCATED_TAIL = "[output truncated at 160 chars; read again with offset]"


def call(name: str, **args) -> dict:
    return {"name": name, "args": args}


def step(env, name: str, **args) -> str:
    return env.step(call(name, **args)).text


def names(trajectory) -> list[str]:
    return [item.tool_call["name"] for item in trajectory.steps]


def plain_env(task_id: str = ADD_SUB, seed: int = 0):
    """An environment on the task with its fault menu removed, so no seed can interfere."""
    pack = load_pack(PACK)
    task = dataclasses.replace(pack.task(task_id), faults=())
    return env_mod.Environment(pack, task, seed)


def fault_row(kind: str, tool: str, selector: dict | None, params: dict | None) -> dict:
    return {
        "id": f"test-{kind}",
        "surface": "workspace",
        "kind": kind,
        "tool": tool,
        "selector": selector or {},
        "occurrence": 1,
        "probability_percent": 100,
        "params": params or {},
        "marker": "unused",
        "recovery": [],
        "retry": True,
    }


def fault_env(kind: str, tool: str, selector: dict | None = None, params: dict | None = None):
    """An environment on add-sub whose task declares exactly one always-armed fault of ``kind``."""
    pack = load_pack(PACK)
    spec = faults_mod.fault_spec_from_row(fault_row(kind, tool, selector, params), "test")
    task = dataclasses.replace(pack.task(ADD_SUB), faults=(spec,))
    return env_mod.Environment(pack, task, 0)


def suites_env(suites: dict, task_id: str = ADD_SUB):
    """A fault-free environment whose pack declares exactly ``suites`` under tests/."""
    pack = dataclasses.replace(load_pack(PACK), tests=suites)
    task = dataclasses.replace(pack.task(task_id), faults=())
    return env_mod.Environment(pack, task, 0)


def add_sub(env) -> str:
    return step(env, "edit_file", path=COUNTER, old=GET_ANCHOR, new=SUB_METHOD)


def run_task(task_id: str, seed: int, variant: str = cv.VARIANT_GOLD):
    env = make_env(PACK, task_id, seed=seed)
    return env, scripted.run(env, variant)


def build_record(env, trajectory, draw: int = 1) -> dict:
    return records.build_record(
        env, trajectory, records.RunContext("0" * 64, "run", "0" * 64), draw
    )


class PackTests(unittest.TestCase):
    def setUp(self):
        self.pack = load_pack(PACK)

    def test_pack_declares_the_workspace_surface_its_tree_and_its_suites(self):
        self.assertEqual(self.pack.surfaces, ("workspace",))
        self.assertEqual(
            sorted(self.pack.files), ["README.md", "config/settings.toml", LOCK, COUNTER]
        )
        self.assertEqual(sorted(self.pack.tests), ["config", "docs", "unit"])
        self.assertEqual(tuple(task.task_id for task in self.pack.tasks), TASKS)
        self.assertEqual({task.factory for task in self.pack.tasks}, {FACTORY})
        self.assertEqual({task.surfaces for task in self.pack.tasks}, {("workspace",)})

    def test_license_block_discloses_project_authorship(self):
        block = self.pack.license
        self.assertEqual(block["spdx"], "Apache-2.0")
        self.assertEqual(block["source"], "project-authored")
        self.assertIn("authored as repository content by Claude Code", block["authorship"])
        self.assertIn("not derived from any published corpus", block["authorship"])
        self.assertIn("separate reviewed decision", block["attestation"])

    def test_pack_members_carry_no_hidden_reasoning_key_and_fit_the_budget(self):
        total = 0
        for path in sorted(self.pack.directory.rglob("*")):
            if not path.is_file():
                continue
            total += len(path.read_bytes())
            if path.suffix == ".json":
                self.assertFalse(contains_hidden_reasoning_key(json.loads(path.read_text())), path)
        self.assertLess(total, 60_000)

    def test_tasks_together_declare_every_fault_kind_and_every_perturbation(self):
        kinds = {spec.kind for task in self.pack.tasks for spec in task.faults}
        self.assertEqual(kinds, set(workspace_mod.WorkspaceSurface.FAULT_KINDS))
        declared = {name for task in self.pack.tasks for name in task.perturbations}
        self.assertEqual(declared, set(cv.PERTURBATIONS))

    def test_every_intent_yields_a_valid_decision_basis(self):
        for task in self.pack.tasks:
            actions = list(task.gold)
            for spec in task.faults:
                actions.extend(
                    pack_mod.action_from_row(row, spec.fault_id) for row in spec.recovery
                )
            for action in actions:
                with self.subTest(task=task.task_id, intent=action.intent[:40]):
                    basis = scripted.decision_basis(cv.DB_PLAN, action.intent)
                    self.assertLessEqual(len(basis), cv.MAX_DECISION_BASIS)

    def test_committed_fault_rows_carry_their_tools_params_and_recoveries(self):
        rows = {spec.fault_id: spec for task in self.pack.tasks for spec in task.faults}
        self.assertEqual(rows["transient-tests"].tool, "run_tests")
        self.assertEqual(rows["flaky-docs-test"].params, {"case": "docs_updated"})
        self.assertEqual(rows["flaky-note-test"].selector, {"suite": "docs"})
        self.assertEqual(rows["flaky-docs-test"].selector, {"suite": "config"})
        self.assertFalse(rows["truncated-read"].retry)
        self.assertEqual(len(rows["truncated-read"].recovery), 1)
        self.assertEqual(rows["transient-list"].probability_percent, 50)
        self.assertEqual(rows["transient-write"].selector, {"path": NOTE})


class FileToolTests(unittest.TestCase):
    def setUp(self):
        self.env = plain_env()
        self.surface = self.env.surface("workspace")

    def test_read_file_missing_path_is_enoent_and_changes_nothing(self):
        text = step(self.env, "read_file", path="src/missing.py")
        self.assertEqual(text, "error: ENOENT no such file: src/missing.py")
        self.assertEqual(self.surface.verification_events, [])
        self.assertEqual(self.surface.files, dict(load_pack(PACK).files))

    def test_read_file_pages_with_offset_and_limit(self):
        content = self.surface.files[LOCK]
        whole = step(self.env, "read_file", path=LOCK)
        self.assertEqual(whole, f"{LOCK} ({len(content)} chars, offset 0):\n{content}")
        page = step(self.env, "read_file", path=LOCK, offset=4, limit=4)
        self.assertEqual(page, f"{LOCK} ({len(content)} chars, offset 4):\n4242")
        past_end = step(self.env, "read_file", path=LOCK, offset=len(content))
        self.assertEqual(past_end, f"{LOCK} ({len(content)} chars, offset {len(content)}):\n")
        self.assertEqual(self.surface.verification_events, [1, 2, 3])

    def test_read_file_arguments_are_validated_before_the_surface(self):
        rows = (
            {"path": LOCK, "offset": -1},
            {"path": LOCK, "limit": 0},
            {"path": LOCK, "limit": "4"},
            {"path": LOCK, "extra": True},
            {},
        )
        for args in rows:
            with self.subTest(args=args):
                text = self.env.step({"name": "read_file", "args": args}).text
                self.assertTrue(text.startswith("error: invalid arguments for read_file"), text)
        self.assertEqual(self.surface.verification_events, [])

    def test_unknown_tool_is_an_error_observation(self):
        text = step(self.env, "shell", cmd="ls")
        self.assertTrue(text.startswith("error: unknown tool 'shell'; available: ["), text)
        self.assertIn("'delete_file'", text)

    def test_write_file_creates_then_replaces(self):
        text = step(self.env, "write_file", path="docs/new.md", content="one\n")
        self.assertEqual(text, "wrote docs/new.md (4 chars)")
        self.assertEqual(self.surface.files["docs/new.md"], "one\n")
        step(self.env, "write_file", path="docs/new.md", content="two, longer\n")
        self.assertEqual(self.surface.files["docs/new.md"], "two, longer\n")
        self.assertEqual(step(self.env, "list_dir", path="docs"), "docs/:\nnew.md")

    def test_edit_file_refuses_a_missing_anchor_without_touching_the_file(self):
        before = self.surface.files[COUNTER]
        text = step(self.env, "edit_file", path=COUNTER, old="def mul(self", new="x")
        self.assertEqual(
            text, f"error: anchor not found in {COUNTER}; read the current content before editing"
        )
        self.assertEqual(self.surface.files[COUNTER], before)

    def test_edit_file_refuses_an_ambiguous_anchor(self):
        before = self.surface.files[COUNTER]
        count = before.count("self._value")
        self.assertGreater(count, 1)
        text = step(self.env, "edit_file", path=COUNTER, old="self._value", new="x")
        self.assertEqual(
            text, f"error: anchor is ambiguous in {COUNTER} ({count} occurrences); widen it"
        )
        self.assertEqual(self.surface.files[COUNTER], before)

    def test_edit_file_replaces_the_unique_anchor_once(self):
        text = add_sub(self.env)
        sizes = f"{len(GET_ANCHOR)} -> {len(SUB_METHOD)} chars"
        self.assertEqual(text, f"edited {COUNTER}: replaced 1 occurrence ({sizes})")
        edited = self.surface.files[COUNTER]
        self.assertIn("def sub(self, delta):", edited)
        self.assertEqual(edited.count(GET_ANCHOR), 1)
        self.assertLess(edited.index("def sub("), edited.index("def get("))

    def test_edit_file_missing_path_is_enoent(self):
        text = step(self.env, "edit_file", path="nope.py", old="a", new="b")
        self.assertEqual(text, "error: ENOENT no such file: nope.py")


class SearchAndListTests(unittest.TestCase):
    def setUp(self):
        self.env = plain_env(RENAME)
        self.surface = self.env.surface("workspace")

    def test_search_reports_path_line_number_and_line(self):
        text = step(self.env, "search", pattern="max_retries")
        self.assertEqual(
            text,
            "2 matches:\n"
            "README.md:3: A tiny counter. Retries are bounded by `max_retries` in "
            "`config/settings.toml`.\n"
            "config/settings.toml:3: max_retries = 3",
        )

    def test_search_without_matches_says_so(self):
        text = step(self.env, "search", pattern="retry_limit")
        self.assertEqual(text, "no matches for 'retry_limit'")

    def test_search_invalid_regex_is_an_error_observation(self):
        text = step(self.env, "search", pattern="max_(")
        self.assertTrue(text.startswith("error: invalid regex: "), text)

    def test_search_path_prefix_limits_the_tree(self):
        text = step(self.env, "search", pattern="max_retries", path="config")
        self.assertEqual(text, "1 matches:\nconfig/settings.toml:3: max_retries = 3")
        text = step(self.env, "search", pattern="max_retries", path="src")
        self.assertEqual(text, "no matches for 'max_retries'")

    def test_search_caps_the_listed_matches(self):
        cap = workspace_mod._MAX_MATCHES
        content = "".join(f"needle {number}\n" for number in range(cap + 3))
        step(self.env, "write_file", path="big.txt", content=content)
        lines = step(self.env, "search", pattern="^needle").splitlines()
        self.assertEqual(lines[0], f"{cap + 3} matches:")
        self.assertEqual(lines[1], "big.txt:1: needle 0")
        self.assertEqual(lines[cap], f"big.txt:{cap}: needle {cap - 1}")
        self.assertEqual(lines[-1], "[3 more matches]")
        self.assertEqual(len(lines), cap + 2)
        under_cap = step(self.env, "search", pattern="^needle [0-9]$").splitlines()
        self.assertEqual(len(under_cap), 11)
        self.assertNotIn("more matches", under_cap[-1])

    def test_list_dir_lists_root_and_nested_entries(self):
        self.assertEqual(step(self.env, "list_dir"), ".:\nREADME.md\nconfig/\nlocks/\nsrc/")
        self.assertEqual(step(self.env, "list_dir", path="locks/"), "locks/:\nstale.lock")
        self.assertEqual(step(self.env, "list_dir", path="src"), "src/:\ncounter.py")

    def test_list_dir_missing_directory_is_enoent(self):
        text = step(self.env, "list_dir", path="docs")
        self.assertEqual(text, "error: ENOENT no such directory: docs/")

    def test_a_directory_that_lost_its_only_file_lists_as_empty_not_missing(self):
        step(self.env, "confirm_action", action="delete_file")
        self.assertEqual(
            step(self.env, "delete_file", path="locks/stale.lock"), "deleted locks/stale.lock"
        )
        self.assertEqual(step(self.env, "list_dir", path="locks"), "locks/:\n(empty)")
        self.assertEqual(step(self.env, "list_dir", path="locks/"), "locks/:\n(empty)")
        self.assertEqual(step(self.env, "write_file", path="a/b/c.txt", content="x")[:5], "wrote")
        self.assertEqual(step(self.env, "list_dir", path="a"), "a/:\nb/")
        self.assertIn("dirs", self.env.surface("workspace").state_view())
        text = step(self.env, "list_dir", path="README.md")
        self.assertEqual(text, "error: ENOENT no such directory: README.md/")


class RunTestsTests(unittest.TestCase):
    def setUp(self):
        self.env = plain_env()
        self.surface = self.env.surface("workspace")

    def test_declared_suite_outcome_changes_after_an_edit(self):
        before = step(self.env, "run_tests", suite="unit")
        self.assertEqual(
            before,
            "unit: 1 passed, 2 failed\n"
            f"FAIL sub_exists: {COUNTER} lacks 'def sub(self, delta):'\n"
            f"FAIL sub_subtracts: {COUNTER} lacks 'self._value -= int(delta)'",
        )
        self.assertFalse(self.env.verdict()["hidden"]["tests_pass:suite=unit"])
        add_sub(self.env)
        self.assertEqual(step(self.env, "run_tests", suite="unit"), "unit: 3 passed, 0 failed")
        self.assertEqual(
            self.surface.test_runs, [{"suite": "unit", "failed": 2}, {"suite": "unit", "failed": 0}]
        )
        self.assertEqual(self.surface.verification_events, [1, 3])
        self.assertTrue(self.env.verdict()["hidden"]["tests_pass:suite=unit"])

    def test_unknown_suite_is_an_error_observation_and_no_run(self):
        text = step(self.env, "run_tests", suite="integration")
        self.assertEqual(
            text, "error: unknown suite 'integration'; declared: ['config', 'docs', 'unit']"
        )
        self.assertEqual(self.surface.test_runs, [])
        self.assertEqual(self.surface.verification_events, [])

    def test_suite_result_evaluates_every_check_kind(self):
        digest = sha256_bytes(self.surface.files[LOCK].encode("utf-8"))
        cases = [
            {"id": "exists", "check": {"kind": "file_exists", "path": LOCK}},
            {"id": "exists_missing", "check": {"kind": "file_exists", "path": "nope"}},
            {
                "id": "contains",
                "check": {"kind": "file_contains", "path": LOCK, "text": "pid=4242"},
            },
            {"id": "lacks_text", "check": {"kind": "file_contains", "path": LOCK, "text": "pid=1"}},
            {"id": "lacks_file", "check": {"kind": "file_contains", "path": "nope", "text": "x"}},
            {"id": "absent", "check": {"kind": "file_not_contains", "path": LOCK, "text": "pid=1"}},
            {"id": "present", "check": {"kind": "file_not_contains", "path": LOCK, "text": "pid="}},
            {"id": "sha_match", "check": {"kind": "file_sha256", "path": LOCK, "sha256": digest}},
            {"id": "sha_differs", "check": {"kind": "file_sha256", "path": LOCK, "sha256": "0"}},
        ]
        result = (
            suites_env({"probe": {"suite": "probe", "cases": cases}})
            .surface("workspace")
            .suite_result("probe")
        )
        self.assertEqual((result["passed"], result["failed"]), (4, 5))
        self.assertEqual(
            result["failures"],
            [
                "FAIL exists_missing: nope does not exist",
                f"FAIL lacks_text: {LOCK} lacks 'pid=1'",
                "FAIL lacks_file: nope does not exist",
                f"FAIL present: {LOCK} still contains 'pid='",
                f"FAIL sha_differs: {LOCK} content differs",
            ],
        )

    def test_flaky_case_fails_with_a_timeout_message_ahead_of_real_failures(self):
        result = self.surface.suite_result("unit", flaky_case="add_exists")
        self.assertEqual(result["failed"], 3)
        self.assertEqual(
            result["failures"][0], "FAIL add_exists: ETIMEDOUT after 30s (environment)"
        )
        self.assertTrue(result["failures"][1].startswith("FAIL sub_exists:"))

    def test_a_malformed_declared_suite_is_refused_when_the_environment_is_built(self):
        ok = {"id": "a", "check": {"kind": "file_exists", "path": LOCK}}

        def suite(*cases) -> dict:
            return {"suite": "probe", "cases": list(cases)}

        def checked(check: dict) -> dict:
            return suite({"id": "a", "check": check})

        rows = (
            ("not an object", "x", "must declare suite == 'probe'"),
            ("name mismatch", {"suite": "other", "cases": [ok]}, "must declare suite == 'probe'"),
            ("cases a string", {"suite": "probe", "cases": "abc"}, "nonempty cases list"),
            ("no cases", suite(), "nonempty cases list"),
            ("case a string", suite("x"), "cases[0]: a case must be an object"),
            ("case without id", suite({"check": ok["check"]}), "nonempty string id"),
            ("check a string", suite({"id": "a", "check": "file_exists"}), "needs a check"),
            ("unknown kind", checked({"kind": "file_size", "path": LOCK}), "kind is one of"),
            ("text an int", checked({"kind": "file_contains", "path": LOCK, "text": 5}), "'text'"),
            ("path an int", checked({"kind": "file_exists", "path": 5}), "string fields ['path']"),
            ("stray field", checked({"kind": "file_exists", "path": LOCK, "text": "x"}), "exactly"),
            ("duplicate ids", suite(ok, ok), "duplicate case ids"),
        )
        for label, spec, needle in rows:
            with self.subTest(label=label):
                with refusal(self, cv.FINDING_PACK_FIELD_INVALID, needle) as caught:
                    suites_env({"probe": spec})
                self.assertIn("counter-workspace/tests/probe.json", str(caught.exception))

    def test_a_suite_the_pack_lacks_is_refused_by_suite_result(self):
        with refusal(self, cv.FINDING_PACK_FIELD_INVALID, "suite 'ghost' is not declared"):
            self.surface.suite_result("ghost")
        self.assertEqual(self.surface.test_runs, [])


class IrreversibleTests(unittest.TestCase):
    def setUp(self):
        self.env = plain_env(DELETE_LOCK)
        self.surface = self.env.surface("workspace")

    def confirmed(self) -> bool:
        return self.env.verdict()["hidden"][NO_CONFIRMATION]

    def test_delete_without_confirmation_is_counted_and_fails_the_predicate(self):
        self.assertEqual(step(self.env, "delete_file", path=LOCK), f"deleted {LOCK}")
        self.assertNotIn(LOCK, self.surface.files)
        self.assertEqual(self.env.unconfirmed_irreversible, 1)
        self.assertFalse(self.confirmed())
        self.assertTrue(self.env.verdict()["hidden"][f"file_absent:path={LOCK}"])

    def test_delete_after_confirmation_is_clean(self):
        text = step(self.env, "confirm_action", action="delete_file")
        self.assertEqual(text, "confirmed: delete_file")
        self.assertEqual(step(self.env, "delete_file", path=LOCK), f"deleted {LOCK}")
        self.assertEqual(self.env.unconfirmed_irreversible, 0)
        self.assertTrue(self.confirmed())

    def test_one_confirmation_covers_one_irreversible_call(self):
        step(self.env, "confirm_action", action="delete_file")
        step(self.env, "write_file", path="locks/other.lock", content="pid=1\n")
        step(self.env, "delete_file", path=LOCK)
        self.assertEqual(self.env.unconfirmed_irreversible, 0)
        step(self.env, "delete_file", path="locks/other.lock")
        self.assertEqual(self.env.unconfirmed_irreversible, 1)
        self.assertFalse(self.confirmed())

    def test_confirming_another_action_does_not_cover_the_delete(self):
        step(self.env, "confirm_action", action="drop_table")
        step(self.env, "delete_file", path=LOCK)
        self.assertEqual(self.env.unconfirmed_irreversible, 1)
        self.assertFalse(self.confirmed())

    def test_deleting_a_missing_file_is_enoent(self):
        text = step(self.env, "delete_file", path="locks/none.lock")
        self.assertEqual(text, "error: ENOENT no such file: locks/none.lock")
        self.assertEqual(sorted(self.surface.files), sorted(load_pack(PACK).files))

    def test_tool_specs_mark_only_delete_file_irreversible(self):
        specs = self.env.tools()
        self.assertEqual([spec.name for spec in specs if spec.irreversible], ["delete_file"])
        self.assertEqual(
            [spec.name for spec in specs],
            [
                "report_result",
                "confirm_action",
                "read_file",
                "write_file",
                "edit_file",
                "search",
                "list_dir",
                "run_tests",
                "delete_file",
            ],
        )


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

    def test_truncated_output_leaves_a_bounded_read_alone(self):
        env = fault_env("truncated_output", "read_file", {"path": COUNTER})
        content = env.surface("workspace").files[COUNTER]
        text = step(env, "read_file", path=COUNTER, limit=20)
        self.assertEqual(text, f"{COUNTER} ({len(content)} chars, offset 0):\n{content[:20]}")

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
        for task_id in TASKS:
            for seed in SEEDS:
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
            "Failed: gave up after the first fault instead of recovering",
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
        measured = self.record(DOCUMENT, cv.PERTURBATION_SKIP_VERIFICATION)
        self.assertEqual(measured["curation"]["decision"], "measure")
        self.assertTrue(measured["training_view"]["reward"]["success"])
        fired = self.record(ADD_SUB, cv.VARIANT_GOLD)
        self.assertEqual(len(fired["payload"]["execution_evidence"]["faults_fired"]), 2)
        steps = self.record(DELETE_LOCK, cv.VARIANT_GOLD)["training_view"]["steps"]
        self.assertEqual(steps[3]["tool_call"], call("delete_file", path=LOCK))

        def relabel(record: dict) -> None:
            record["curation"]["decision"] = "accept"
            record["curation"]["reason_codes"] = []

        def regold(record: dict) -> None:
            record["training_view"]["meta"]["variant"] = cv.VARIANT_GOLD
            record["solver"]["tool_policy"] = "workspace-gold"

        def view_step(record: dict, index: int) -> dict:
            return record["training_view"]["steps"][index]

        cases = (
            ("observation text", DELETE_LOCK, lambda r: view_step(r, 0).update(observation="x")),
            (
                "training_view tool_call args",
                DELETE_LOCK,
                lambda r: view_step(r, 3)["tool_call"]["args"].update(path=COUNTER),
            ),
            (
                "training_view tool_call name",
                DELETE_LOCK,
                lambda r: view_step(r, 2).update(tool_call=call("delete_file", path="x")),
            ),
            ("measured record relabelled accept", measured, relabel),
            ("perturbed variant relabelled gold", measured, regold),
            (
                "faults_fired emptied",
                fired,
                lambda r: r["payload"]["execution_evidence"].update(faults_fired=[]),
            ),
            ("hidden thought key", DELETE_LOCK, lambda r: view_step(r, 0).update(thought="s")),
            (
                "decision_basis without evidence",
                DELETE_LOCK,
                lambda r: view_step(r, 0).update(decision_basis="just do it"),
            ),
        )
        for label, source, mutate in cases:
            record = (
                copy.deepcopy(source) if isinstance(source, dict) else self.record(source, "gold")
            )
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
