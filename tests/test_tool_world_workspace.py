#!/usr/bin/env python3
"""The counter-workspace pack and the file, search, and list tools of the workspace surface."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tool_world_test_support import cv, load_pack, pack_mod
from tool_world_workspace_support import (
    COUNTER,
    FACTORY,
    GET_ANCHOR,
    LOCK,
    NOTE,
    PACK,
    RENAME,
    SUB_METHOD,
    TASKS,
    add_sub,
    plain_env,
    step,
)

# The support modules go first: they put pipelines/ on sys.path for the imports below.
# isort: split
from tool_world._contract import contains_hidden_reasoning_key
from tool_world.policies import scripted
from tool_world.surfaces import workspace as workspace_mod
from tool_world.surfaces import workspace_search


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

    def test_search_refuses_a_pattern_shaped_to_backtrack_without_bound(self):
        nested = ("(a+)+$", "(a|aa)*b", "((x*)y){2,}", "(\\d+|\\w+)+:", "(?:a?)+", "(a{2,}b)*")
        for pattern in nested:
            with self.subTest(pattern=pattern):
                text = step(self.env, "search", pattern=pattern)
                self.assertTrue(text.startswith("error: regex nests repetition"), text)
        cap = workspace_search.MAX_PATTERN_CHARS
        self.assertEqual(
            step(self.env, "search", pattern="a" * (cap + 1)),
            f"error: regex longer than {cap} chars",
        )

    def test_search_accepts_repetition_that_is_not_nested(self):
        env = plain_env(RENAME)
        for pattern in ("(ab)+c", "[(+]+", "\\(a+\\)+", "a{2,3}(b|c)", "(?:re)*tries", "(a+){"):
            with self.subTest(pattern=pattern):
                text = step(env, "search", pattern=pattern)
                self.assertFalse(text.startswith("error"), text)

    def test_search_path_prefix_limits_the_tree(self):
        text = step(self.env, "search", pattern="max_retries", path="config")
        self.assertEqual(text, "1 matches:\nconfig/settings.toml:3: max_retries = 3")
        text = step(self.env, "search", pattern="max_retries", path="src")
        self.assertEqual(text, "no matches for 'max_retries'")

    def test_search_caps_the_listed_matches(self):
        cap = workspace_search.MAX_MATCHES
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


if __name__ == "__main__":
    unittest.main()
