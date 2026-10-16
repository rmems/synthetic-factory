"""Branch coverage for ``evh.catalog_ast``: the closed literal resolver stays closed."""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from evh.catalog_ast import (
    UNSET,
    assignment_of,
    call_name,
    extract_joined_path_assignment,
    function_named,
    joined_path_constant,
    require,
    resolve,
)

ENV = {"s": "ab-c", "n": 7, "lst": [1, 2, 3], "d": {"k": 1}}


def expr(source: str) -> ast.AST:
    return ast.parse(source, mode="eval").body


def stmt(source: str) -> ast.stmt:
    return ast.parse(source).body[0]


class AssignmentAndCallNameTests(unittest.TestCase):
    def test_assignment_forms(self) -> None:
        name, value = assignment_of(stmt("x: int = 1"))
        self.assertEqual((name, value.value), ("x", 1))
        for source in ("a = b = 1", "a.b = 1", "a += 1"):
            with self.subTest(source=source):
                self.assertEqual(assignment_of(stmt(source)), (None, None))

    def test_call_name(self) -> None:
        self.assertEqual(call_name(expr("foo(1)")), "foo")
        self.assertIsNone(call_name(expr("a.foo(1)")))
        self.assertIsNone(call_name(expr("foo")))


class ResolveResolvedTests(unittest.TestCase):
    CASES = (
        ("-n", -7),
        ("{1, 2}", {1, 2}),
        ("{'a': n}", {"a": 7}),
        ("f'x{n}{s!s}'", "x7ab-c"),
        ("'a' + s", "aab-c"),
        ("n + 1", 8),
        ("n - 2", 5),
        ("n // 2", 3),
        ("lst[1:]", [2, 3]),
        ("lst[::2]", [1, 3]),
        ("d['k']", 1),
        ("pair(1, s)", (1, "ab-c")),
        ("s.replace('-', '_')", "ab_c"),
        ("s.title()", "Ab-C"),
        ("s.upper()", "AB-C"),
    )

    def test_closed_forms_resolve(self) -> None:
        for source, expected in self.CASES:
            with self.subTest(source=source):
                self.assertEqual(resolve(expr(source), ENV), expected)


class ResolveUnsetTests(unittest.TestCase):
    CASES = (
        "-s", "{1, x}", "{**d}", "{x: 1}", "{'a': x}",
        "f'{s!r}'", "f'{n:>3}'", "f'{lst}'", "f'{x}'",
        "x + 1", "'a' + 1", "n * 2",
        "x[0]", "lst[x:]", "lst[:x]", "lst[::x]", "n[1:2]", "lst[x]", "lst[9]", "d['z']",
        "eval('1')", "exec('1')", "pair(x)", "pair(1, k=2)", "foo()",
        "s.lower()", "n.upper()", "s.upper(x)", "s.upper(k=1)", "s.replace('a', 1)",
        "s.title(1)", "s.replace('a')", "lambda: 1",
    )

    def test_everything_else_stays_unset(self) -> None:
        for source in self.CASES:
            with self.subTest(source=source):
                self.assertIs(resolve(expr(source), ENV), UNSET)

    def test_joined_str_with_non_string_part_is_unset(self) -> None:
        node = ast.JoinedStr(values=[ast.Constant(value=1)])
        self.assertIs(resolve(node, ENV), UNSET)

    def test_no_env_means_names_are_unset(self) -> None:
        self.assertIs(resolve(expr("n")), UNSET)


class ResolveSliceNodeTests(unittest.TestCase):
    @staticmethod
    def slice_of(source: str) -> ast.AST:
        return expr(source).slice

    def test_bare_slice_node_resolves_to_slice(self) -> None:
        self.assertEqual(resolve(self.slice_of("lst[1:n:2]"), ENV), slice(1, 7, 2))
        self.assertEqual(resolve(self.slice_of("lst[:]"), ENV), slice(None))

    def test_bare_slice_node_with_unresolved_bound_is_unset(self) -> None:
        for source in ("lst[x:]", "lst[:x]", "lst[::x]"):
            with self.subTest(source=source):
                self.assertIs(resolve(self.slice_of(source), ENV), UNSET)


class RequireTests(unittest.TestCase):
    def test_require_returns_resolved_value(self) -> None:
        self.assertEqual(require(expr("n"), ENV, "ctx"), 7)

    def test_require_refuses_unresolved_with_line(self) -> None:
        node = expr("x")
        with self.assertRaisesRegex(ValueError, r"^catalog: cannot resolve AST at line 1$"):
            require(node, ENV, "catalog")

    def test_require_without_lineno_reports_question_mark(self) -> None:
        node = ast.Name(id="x")
        with self.assertRaisesRegex(ValueError, r"at line \?$"):
            require(node, ENV, "catalog")


class JoinedPathTests(unittest.TestCase):
    CASES = (
        ("ROOT / 'scripts' / 'mill'", "scripts/mill"),
        ("'a' / 'b'", "a/b"),
        ("'a' / ROOT", None),
        ("ROOT", None),
        ("'a' + 'b'", None),
        ("3", None),
    )

    def test_joined_path_constant(self) -> None:
        for source, expected in self.CASES:
            with self.subTest(source=source):
                self.assertEqual(joined_path_constant(expr(source)), expected)

    def test_extract_joined_path_assignment(self) -> None:
        source = "import os\nOTHER = 1\nMILL = ROOT / 'scripts' / 'm.py'\n"
        self.assertEqual(extract_joined_path_assignment(source, "MILL"), "scripts/m.py")
        self.assertIsNone(extract_joined_path_assignment(source, "MISSING"))
        self.assertIsNone(extract_joined_path_assignment("MILL: str\n", "MILL"))


class FunctionNamedTests(unittest.TestCase):
    def test_function_named(self) -> None:
        tree = ast.parse("X = 1\nasync def build():\n    pass\ndef build():\n    pass\n")
        self.assertIsInstance(function_named(tree, "build"), ast.FunctionDef)
        self.assertIsNone(function_named(tree, "missing"))
        self.assertIsNone(function_named(expr("1"), "build"))


if __name__ == "__main__":
    unittest.main()
