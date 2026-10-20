"""search.catalog_ast.literal_value: every node shape it resolves, and its recursion budget."""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from search.catalog_ast import (
    UNSET,
    assignment_names,
    assignment_of,
    literal_value,
    module_docstring,
)


def _value(source: str, env=None):
    return literal_value(ast.parse(source, mode="eval").body, env)


def _statement(source: str) -> ast.stmt:
    return ast.parse(source).body[0]


class AssignmentTests(unittest.TestCase):
    def test_assignment_of_reads_one_plain_name_target(self):
        name, value = assignment_of(_statement("LIMIT = 8"))
        self.assertEqual(name, "LIMIT")
        self.assertEqual(ast.literal_eval(value), 8)
        name, value = assignment_of(_statement("LIMIT: int = 8"))
        self.assertEqual(name, "LIMIT")
        self.assertEqual(ast.literal_eval(value), 8)
        self.assertEqual(assignment_of(_statement("LIMIT: int")), ("LIMIT", None))

    def test_assignment_of_refuses_every_other_shape(self):
        for source in ("A = B = 1", "A, B = 1, 2", "obj.attr = 1", "obj.attr: int = 1", "f()"):
            with self.subTest(source=source):
                self.assertEqual(assignment_of(_statement(source)), (None, None))

    def test_assignment_names_lists_every_plain_name_target(self):
        cases = (
            ("A = B = 1", ("A", "B")),
            ("A = obj.attr = 1", ("A",)),
            ("A, B = 1, 2", ()),
            ("LIMIT: int = 8", ("LIMIT",)),
            ("obj.attr: int = 1", ()),
            ("A += 1", ()),
            ("f()", ()),
        )
        for source, names in cases:
            with self.subTest(source=source):
                self.assertEqual(assignment_names(_statement(source)), names)


class ModuleDocstringTests(unittest.TestCase):
    def test_returns_the_raw_module_docstring(self):
        tree = ast.parse('"""  Doc.\n    indented"""\nX = 1')
        self.assertEqual(module_docstring(tree), "  Doc.\n    indented")
        self.assertEqual(module_docstring(ast.parse('""""""')), "")

    def test_no_string_docstring_reads_as_empty(self):
        for source in ("", "X = 1", "1", "b'bytes'", "f'{x}'"):
            with self.subTest(source=source):
                self.assertEqual(module_docstring(ast.parse(source)), "")

    def test_non_modules_read_as_empty(self):
        function = _statement('def f():\n    """Doc."""')
        self.assertEqual(module_docstring(function), "")
        self.assertEqual(module_docstring(ast.parse("1", mode="eval")), "")


class LiteralValueLeafTests(unittest.TestCase):
    def test_constants_resolve_to_their_value(self):
        self.assertEqual(_value("'text'"), "text")
        self.assertEqual(_value("3"), 3)
        self.assertIsNone(_value("None"))

    def test_names_resolve_only_when_bound(self):
        self.assertEqual(_value("LIMIT", {"LIMIT": 8}), 8)
        self.assertIs(_value("LIMIT", {"OTHER": 8}), UNSET)
        self.assertIs(_value("LIMIT"), UNSET)
        self.assertIs(_value("LIMIT", {}), UNSET)

    def test_unary_minus_negates_numbers_only(self):
        self.assertEqual(_value("-4"), -4)
        self.assertEqual(_value("-1.5"), -1.5)
        self.assertEqual(_value("-True"), -1)
        self.assertEqual(_value("-N", {"N": 2}), -2)
        self.assertIs(_value("-'a'"), UNSET)
        self.assertIs(_value("-N"), UNSET)

    def test_other_operators_and_calls_are_unset(self):
        self.assertIs(_value("+1"), UNSET)
        self.assertIs(_value("~1"), UNSET)
        self.assertIs(_value("1 + 2"), UNSET)
        self.assertIs(_value("f(1)"), UNSET)


class LiteralValueContainerTests(unittest.TestCase):
    def test_each_sequence_keeps_its_own_container_type(self):
        as_tuple = _value("(1, -2, 'x')")
        as_list = _value("[1, -2, 'x']")
        as_set = _value("{1, -2, 'x'}")
        self.assertIsInstance(as_tuple, tuple)
        self.assertEqual(as_tuple, (1, -2, "x"))
        self.assertIsInstance(as_list, list)
        self.assertEqual(as_list, [1, -2, "x"])
        self.assertIsInstance(as_set, set)
        self.assertEqual(as_set, {1, -2, "x"})

    def test_one_unresolved_item_makes_the_sequence_unset(self):
        for source in ("(1, X)", "[1, X]", "{1, X}"):
            with self.subTest(source=source):
                self.assertIs(_value(source), UNSET)
        self.assertEqual(_value("{1, X}", {"X": 2}), {1, 2})

    def test_an_unhashable_set_member_raises_like_set_does(self):
        with self.assertRaisesRegex(TypeError, "unhashable type: 'list'"):
            _value("{(1, [2])}")

    def test_dicts_resolve_keys_and_values(self):
        self.assertEqual(
            _value("{'a': 1, 'b': [1, (2, 3)], K: {4}}", {"K": "k"}),
            {"a": 1, "b": [1, (2, 3)], "k": {4}},
        )
        self.assertIs(_value("{'a': X}"), UNSET)
        self.assertIs(_value("{X: 1}"), UNSET)
        self.assertIs(_value("{**X, 'a': 1}", {"X": {}}), UNSET)

    def test_nested_containers_resolve_to_the_parser_limit(self):
        depth = 150
        value = _value("[" * depth + "1" + "]" * depth)
        for _ in range(depth):
            self.assertIsInstance(value, list)
            self.assertEqual(len(value), 1)
            value = value[0]
        self.assertEqual(value, 1)


class LiteralValueRecursionBudgetTests(unittest.TestCase):
    """One frame per ``-`` level, so a 600-deep chain resolves as it does on main."""

    def test_a_600_deep_minus_chain_resolves(self):
        self.assertEqual(_value("-" * 600 + "1"), 1)
        self.assertEqual(_value("-" * 601 + "1"), -1)

    def test_a_600_deep_minus_chain_over_a_name_resolves(self):
        self.assertEqual(_value("-" * 600 + "N", {"N": 3}), 3)
        self.assertIs(_value("-" * 600 + "N"), UNSET)

    def test_150_containers_around_a_600_deep_minus_chain_resolve(self):
        """Two frames per container level, as on main: 150 levels plus 600 minus signs fit."""

        depth = 150
        cases = (
            ("[" * depth + "-" * 600 + "1" + "]" * depth, 0),
            ("{0:" * depth + "-" * 600 + "1" + "}" * depth, 0),
        )
        for source, key in cases:
            with self.subTest(opener=source[0]):
                value = _value(source)
                for _ in range(depth):
                    value = value[key]
                self.assertEqual(value, 1)


if __name__ == "__main__":
    unittest.main()
