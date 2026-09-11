#!/usr/bin/env python3
"""The code-repair family vocabulary: declared codes, identities, label policy, refusals."""

import ast
import inspect
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from code_repair_test_support import (  # noqa: E402
    FAMILY_MODULES, envelope, oc, refusal, vocabulary as cv,
)


def random_import_call(node):
    """Whether a call uses an import_module attribute with a literal random argument."""
    if not isinstance(node.func, ast.Attribute):
        return False
    if node.func.attr != "import_module" or not node.args:
        return False
    argument = node.args[0]
    return isinstance(argument, ast.Constant) and argument.value == "random"


def random_import(node):
    """Whether an AST node directly imports random, including importlib calls."""
    if isinstance(node, ast.Import):
        return any(item.name == "random" for item in node.names)
    if isinstance(node, ast.ImportFrom):
        return node.module == "random"
    if isinstance(node, ast.Call):
        return random_import_call(node)
    return False


class DeclaredCodes(unittest.TestCase):
    def test_export_integrity_codes_are_declared_and_unique(self):
        expected = {"REPLAY_FILE_MALFORMED", "REPLAY_RUN_IDENTITY_MISMATCH",
                    "EXPORT_CATALOG_MISMATCH", "RUN_SUMMARY_MISMATCH"}
        self.assertLessEqual(expected, set(cv.EXPORT_INTEGRITY_CODES))
        self.assertEqual(len(cv.EXPORT_CODES), len(set(cv.EXPORT_CODES)))
    def test_random_import_detector_preserves_import_and_call_boundaries(self):
        cases = (
            ("import random", True),
            ("import math, random as rng", True),
            ("from random import choice", True),
            ("importlib.import_module('random')", True),
            ("loader.import_module('random')", True),
            ("import math", False),
            ("from math import floor", False),
            ("importlib.import_module('math')", False),
            ("importlib.import_module()", False),
            ("importlib.import_module(name)", False),
            ("importlib.other('random')", False),
            ("import_module('random')", False),
            ("value = 'random'", False),
        )
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(any(random_import(node) for node in ast.walk(ast.parse(source))),
                                 expected)

    def test_every_code_family_is_unique_and_disjoint(self):
        families = (cv.REASON_CODES, cv.FINDING_CODES, cv.SKIP_CODES, cv.LEAK_CODES)
        for codes in families:
            with self.subTest(codes=codes[:1]):
                self.assertEqual(len(codes), len(set(codes)))
        self.assertFalse(cv.REASON_CODE_SET & cv.FINDING_CODE_SET)
        self.assertFalse(cv.SKIP_CODE_SET & cv.FINDING_CODE_SET)
        self.assertFalse(cv.LEAK_CODE_SET & cv.FINDING_CODE_SET)
        self.assertIn(cv.REASON_ORIGINAL_FAILS_PUBLIC, cv.CHECK_CODE_SET)

    def test_the_family_is_registered_with_the_shared_contract(self):
        self.assertIn(cv.FAMILY, oc.FAMILIES)
        self.assertIn(cv.FAMILY, oc.declared_families())
        self.assertIs(oc.oracle_label_policy(cv.FAMILY), cv.ORACLE_LABEL_POLICY)
        self.assertEqual(cv.ORACLE_LABEL_POLICY.label_keys, cv.ORACLE_LABEL_KEYS)
        for quantity in ("passed_check_count", "failed_check_count"):
            self.assertEqual(oc.QUANTITY_UNITS[quantity], "count")
            self.assertIn(quantity, oc.NON_NEGATIVE_QUANTITIES)

    def test_identity_strings_are_the_chosen_literals(self):
        self.assertEqual(cv.GENERATOR_NAME, "python-repair-mutator")
        self.assertEqual(cv.ORACLE_IMPLEMENTATION, "pipelines/code_repair/_harness.py:main")
        self.assertEqual(cv.PRODUCER, "pipelines/code_repair/records.py")
        self.assertEqual(cv.RECORD_KIND, "issue_patch_v1")
        self.assertEqual(cv.ORACLE_TYPE, "measured_execution")
        self.assertIn(cv.ORACLE_TYPE, oc.ORACLE_TYPES)
        self.assertNotIn(cv.METER, oc.MODELED_METERS)

    def test_label_keys_never_collide_with_generator_keys_or_reserved_names(self):
        scenario_keys = {
            "record_kind", "task_specification", "language", "source", "broken_program",
            "public_tests", "examples", "example_id", "want", "files", "sha256", "kind",
            "operator", "site", "variant", "draw_index", "predicted_repair", "method",
        }
        self.assertFalse(cv.ORACLE_LABEL_KEYS & scenario_keys)
        self.assertFalse(scenario_keys & oc.ORACLE_ONLY_KEYS)
        self.assertIn("outcome", cv.ORACLE_LABEL_KEYS)

    def test_no_family_module_imports_the_random_module(self):
        for name in FAMILY_MODULES:
            module = sys.modules[f"code_repair.{name}"]
            with self.subTest(module=module.__name__):
                tree = ast.parse(inspect.getsource(module))
                self.assertFalse(any(random_import(node) for node in ast.walk(tree)))


class CodedRefusals(unittest.TestCase):
    def test_a_refusal_is_a_contract_error_under_both_spellings(self):
        exc = cv.RepairRefusal(cv.FINDING_INPUT_NOT_AN_OBJECT, "row must be an object")
        self.assertIsInstance(exc, envelope.ContractError)
        self.assertIsInstance(exc, oc.ContractError)
        self.assertIsInstance(exc, oc.CodedRefusal)
        self.assertEqual(str(exc), "INPUT_NOT_AN_OBJECT: row must be an object")

    def test_an_undeclared_code_is_a_programming_error(self):
        with self.assertRaises(LookupError):
            cv.RepairRefusal("NOT_A_CODE", "x")
        with self.assertRaises(LookupError):
            cv.refuse(cv.REASON_MUTANT_TIMEOUT, "a reason code is not a finding code")

    def test_the_refusal_helper_asserts_exactly_one_code(self):
        with refusal(self, cv.FINDING_SEED_NOT_AN_INTEGER, "seed"):
            cv.refuse(cv.FINDING_SEED_NOT_AN_INTEGER, "seed must be an integer")
        self.assertEqual(cv.finding_code("SEED_OUT_OF_DOMAIN: x"), "SEED_OUT_OF_DOMAIN")
        self.assertIsNone(cv.finding_code("MUTANT_TIMEOUT: not a finding"))
        self.assertEqual(cv.shown(10**5000), "an unprintable int of 16610 bits")


if __name__ == "__main__":
    unittest.main()
