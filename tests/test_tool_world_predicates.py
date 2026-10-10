#!/usr/bin/env python3
"""The closed predicate vocabulary: declarations, evaluation on the pack, and refusals."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tool_world_pack_support import ADD_SUB, DELETE_LOCK, call, plain_env, refusal

# The support module goes first: it puts pipelines/ on sys.path for the imports below.
# isort: split
from tool_world import predicates
from tool_world import vocabulary as cv
from tool_world._contract import sha256_bytes

WORKSPACE_PARAMS = {
    "tests_pass": {"suite": "unit"},
    "file_sha256": {
        "path": "locks/stale.lock",
        "sha256": sha256_bytes(b"pid=4242 started=2026-01-01T00:00:00Z\n"),
    },
    "file_contains": {"path": "README.md", "text": "counter"},
    "file_exists": {"path": "README.md"},
    "file_absent": {"path": "missing.txt"},
    "value_reported": {"value": "x"},
    "max_steps": {"n": 3},
    "no_irreversible_without_confirmation": {},
}
FILE_NAMES = frozenset({"tests_pass", "file_sha256", "file_contains", "file_exists", "file_absent"})
# The workspace predicates that hold on the untouched delete-stale-lock task; the rest are False.
TRUE_ON_THE_FRESH_TASK = frozenset(
    {
        "file_sha256",
        "file_contains",
        "file_exists",
        "file_absent",
        "max_steps",
        "no_irreversible_without_confirmation",
    }
)
FOREIGN_PARAMS = {
    "resource_read": {"server": "s", "uri": "u"},
    "tool_called": {"server": "s", "tool": "t"},
    "listed_before_call": {"server": "s"},
    "server_value": {"server": "s", "key": "k", "value": "v"},
    "url_is": {"url": "u"},
    "extracted_equals": {"value": "v"},
    "form_submitted": {"form": "f"},
    "verified_before_merge": {},
    "no_agents_pending": {},
    "max_agents": {"n": 1},
}
BAD_DECLARATIONS = (
    (
        "tests_green",
        {},
        cv.FINDING_PREDICATE_UNKNOWN,
        "row: unknown predicate 'tests_green'",
    ),
    ("tests_pass", {}, cv.FINDING_TASK_FIELD_INVALID, "needs suite as str"),
    ("max_steps", {"n": True}, cv.FINDING_TASK_FIELD_INVALID, "needs n as int"),
    ("max_steps", {"n": 1, "m": 2}, cv.FINDING_TASK_FIELD_INVALID, "does not take ['m']"),
    (
        "file_sha256",
        {"path": 1},
        cv.FINDING_TASK_FIELD_INVALID,
        "row: predicate file_sha256 needs path as str; predicate file_sha256 needs sha256",
    ),
    ("url_is", {"url": "/"}, cv.FINDING_SURFACE_UNKNOWN, "needs the browser surface"),
)
BAD_PARAMS = (
    ("tests_pass", {"suite": 3}, "needs suite as str"),
    ("max_steps", {"n": True}, "needs n as int"),
    ("max_steps", {}, "needs n as int"),
    ("file_sha256", {"path": "README.md"}, "needs sha256 as str"),
    ("value_reported", {"value": None}, "needs value as str"),
)
FIXED_COUNTER = "def add(self, delta):\ndef sub(self, delta):\n    self._value -= int(delta)\n"


class Predicates(unittest.TestCase):
    def test_the_tables_cover_the_closed_vocabulary(self):
        self.assertEqual(
            set(WORKSPACE_PARAMS) | set(FOREIGN_PARAMS), set(predicates.PREDICATE_NAMES)
        )
        self.assertEqual(set(WORKSPACE_PARAMS) & set(FOREIGN_PARAMS), set())
        self.assertGreaterEqual(set(WORKSPACE_PARAMS), TRUE_ON_THE_FRESH_TASK)

    def test_every_predicate_declares_its_surface_and_parameters(self):
        self.assertEqual(set(predicates.PREDICATE_SPECS), set(predicates.PREDICATE_NAMES))
        for name, params in {**WORKSPACE_PARAMS, **FOREIGN_PARAMS}.items():
            surface, declared = predicates.PREDICATE_SPECS[name]
            with self.subTest(predicate=name):
                self.assertEqual(set(declared), set(params))
                self.assertIn(surface, (None, *cv.SURFACES))
                if name in WORKSPACE_PARAMS:
                    self.assertEqual(surface, "workspace" if name in FILE_NAMES else None)
                predicates.check_declaration(name, params, cv.SURFACES, "row")
        self.assertIsNone(predicates.PREDICATE_SPECS["max_steps"][0])
        self.assertEqual(predicates.PREDICATE_SPECS["url_is"][0], "browser")

    def test_check_declaration_refuses_what_the_loader_must_not_accept(self):
        for name, params, code, needle in BAD_DECLARATIONS:
            with self.subTest(predicate=name, params=params), refusal(self, code, needle):
                predicates.check_declaration(name, params, ("workspace",), "row")
        predicates.check_declaration("max_steps", {"n": 1}, (), "row")

    def test_every_workspace_predicate_evaluates_to_a_bool_on_the_pack(self):
        env = plain_env(DELETE_LOCK)
        for name, params in WORKSPACE_PARAMS.items():
            with self.subTest(predicate=name):
                verdict = predicates.evaluate(name, params, env)
                self.assertIs(verdict, name in TRUE_ON_THE_FRESH_TASK)

    def test_every_foreign_predicate_refuses_the_surface_the_task_lacks(self):
        env = plain_env(DELETE_LOCK)
        for name, params in FOREIGN_PARAMS.items():
            with self.subTest(predicate=name), refusal(self, cv.FINDING_SURFACE_UNKNOWN, "has no"):
                predicates.evaluate(name, params, env)

    def test_unknown_predicate_and_bad_params_are_refused(self):
        env = plain_env(DELETE_LOCK)
        with refusal(self, cv.FINDING_PREDICATE_UNKNOWN, "unknown predicate 'tests_green'"):
            predicates.evaluate("tests_green", {}, env)
        for name, params, needle in BAD_PARAMS:
            with self.subTest(predicate=name), refusal(self, cv.FINDING_TASK_FIELD_INVALID, needle):
                predicates.evaluate(name, params, env)

    def test_predicates_follow_the_state_the_tools_change(self):
        env = plain_env(ADD_SUB)
        self.assertFalse(predicates.evaluate("tests_pass", {"suite": "unit"}, env))
        env.step(call("write_file", path="src/counter.py", content=FIXED_COUNTER))
        self.assertTrue(predicates.evaluate("tests_pass", {"suite": "unit"}, env))
        written = env.surface("workspace").files["src/counter.py"].encode("utf-8")
        digest_params = {"path": "src/counter.py", "sha256": sha256_bytes(written)}
        self.assertTrue(predicates.evaluate("file_sha256", digest_params, env))
        env.step(call(cv.TOOL_REPORT, value="x"))
        self.assertTrue(predicates.evaluate("value_reported", {"value": "x"}, env))
        self.assertFalse(predicates.evaluate("value_reported", {"value": "y"}, env))
        self.assertTrue(predicates.evaluate("max_steps", {"n": 2}, env))
        self.assertFalse(predicates.evaluate("max_steps", {"n": 1}, env))
        with refusal(self, cv.FINDING_PACK_FIELD_INVALID, "must declare a cases list"):
            predicates.evaluate("tests_pass", {"suite": "nope"}, env)

    def test_evaluate_all_labels_params_in_sorted_order(self):
        env = plain_env(DELETE_LOCK)
        rows = (
            ("file_contains", {"text": "counter", "path": "README.md"}),
            ("no_irreversible_without_confirmation", {}),
        )
        self.assertEqual(
            predicates.evaluate_all(rows, env),
            {
                "file_contains:path=README.md,text=counter": True,
                "no_irreversible_without_confirmation": True,
            },
        )
        self.assertEqual(predicates.evaluate_all((), env), {})


if __name__ == "__main__":
    unittest.main()
