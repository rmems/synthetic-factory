"""Pin the LHC w4cl literal evaluator, plants-mk-fn extract and header encoder.

``literal_value`` recurses directly for unary minus (one frame per level) and
through ``_sequence`` / ``_mapping`` for containers (two frames per level);
``_encode`` recurses directly. The depth tests hold each at the nesting it
resolved before the split.
"""

from __future__ import annotations

import ast
import importlib
import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

last = importlib.import_module("lhc_w4cl.catalog_ast")
lex = importlib.import_module("lhc_w4cl.catalog_extract")
UNSET = last.UNSET
PATH = "experiments/lhc-mill-w4cl-r4605.py"


def _expr(source: str) -> ast.expr:
    return ast.parse(source, mode="eval").body


def _nested(depth: int, wrap, leaf: ast.expr) -> ast.expr:
    node = leaf
    for _ in range(depth):
        node = wrap(node)
    return node


def _nested_value(depth: int, wrap):
    value = 1
    for _ in range(depth):
        value = wrap(value)
    return value


class LiteralValue(unittest.TestCase):
    def test_values(self):
        self.assertEqual(last.literal_value(_expr("(1, [-2, X], {'k': 'v'})"), {"X": "x"}), (1, [-2, "x"], {"k": "v"}))
        self.assertIs(last.literal_value(None), UNSET)
        for source in ("[1, Y]", "(Y,)", "{'k': Y}", "{**rest}", "-'s'", "{1}", "f(1)"):
            with self.subTest(source=source):
                self.assertIs(last.literal_value(_expr(source)), UNSET)

    def test_depth_600_for_unary_minus_and_400_for_containers(self):
        neg = _nested(600, lambda n: ast.UnaryOp(op=ast.USub(), operand=n), ast.Constant(3))
        self.assertEqual(last.literal_value(neg), 3)
        lists = _nested(400, lambda n: ast.List(elts=[n], ctx=ast.Load()), ast.Constant(1))
        self.assertEqual(last.literal_value(lists), _nested_value(400, lambda v: [v]))
        tuples = _nested(400, lambda n: ast.Tuple(elts=[n], ctx=ast.Load()), ast.Constant(1))
        self.assertEqual(last.literal_value(tuples), _nested_value(400, lambda v: (v,)))
        dicts = _nested(400, lambda n: ast.Dict(keys=[ast.Constant("k")], values=[n]), ast.Constant(1))
        self.assertEqual(last.literal_value(dicts), _nested_value(400, lambda v: {"k": v}))


class PlantsAndPairs(unittest.TestCase):
    def plants(self, source: str):
        return lex._mk_plants(ast.parse(source), path=PATH)

    def test_plants_table(self):
        rows = self.plants("PLANTS = {'a': mk(True, 'slug-a', 'plant-a', 9), 'b': mk(False, 'slug-b', 'plant-b')}")
        self.assertEqual(
            rows,
            [
                {"key": "a", "ok": True, "slug": "slug-a", "plant": "plant-a"},
                {"key": "b", "ok": False, "slug": "slug-b", "plant": "plant-b"},
            ],
        )
        cases = {
            "OTHER = {}": "PLANTS assignment is missing",
            "PLANTS: dict": "PLANTS is not a non-empty dict",
            "PLANTS = {}": "PLANTS is not a non-empty dict",
            "PLANTS = [mk(True, 's', 'p')]": "PLANTS is not a non-empty dict",
            "PLANTS = {'a': mk(True, 's', 'p'), 'b': mk(1, 's', 'p')}": r"PLANTS\[1\] is not a literal mk\(\) plant",
            "PLANTS = {'': mk(True, 's', 'p')}": r"PLANTS\[0\] is not",
            "PLANTS = {**base, 'a': mk(True, 's', 'p')}": r"PLANTS\[0\] is not",
        }
        for source, message in cases.items():
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, f"{PATH} {message}"):
                self.plants(source)

    def test_mk_identity_rejects_anything_but_literal_ok_slug_plant(self):
        for source in (
            "make(True, 's', 'p')", "mk(True, 's')", "mk(True, 's', P)", "mk(1, 's', 'p')",
            "mk(True, '', 'p')", "mk(True, 's', '')", "mk(True, 's', 2)", "x",
        ):
            with self.subTest(source=source):
                self.assertIsNone(lex._mk_identity(_expr(source)))

    def test_pairs_table(self):
        plants = self.plants("PLANTS = {'a': mk(True, 'sa', 'pa'), 'b': mk(False, 'sb', 'pb')}")
        tree = ast.parse("LHC_PAIRS = [('Title', fn('a'), fn('b'), 1, 2, 3)]")
        self.assertEqual(
            lex._fn_pairs(tree, plants, path=PATH),
            [{
                "title": "Title", "success_key": "a", "fail_key": "b", "success_slug": "sa",
                "fail_slug": "sb", "success_plant": "pa", "fail_plant": "pb",
            }],
        )
        cases = {
            "x = 1": "LHC_PAIRS assignment is missing",
            "LHC_PAIRS = []": "LHC_PAIRS is not a non-empty list",
            "LHC_PAIRS = [('T', fn('a'), fn('zz'), 1, 2, 3)]": r"LHC_PAIRS\[0\] is not a fn\(\) identity pair",
        }
        for source, message in cases.items():
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, f"{PATH} {message}"):
                lex._fn_pairs(ast.parse(source), plants, path=PATH)

    def test_pair_identity_needs_a_title_and_two_catalogued_sides(self):
        plants = {"a": {"slug": "sa", "plant": "pa"}, "b": {"slug": "sb", "plant": "pb"}}
        for source in (
            "('T', fn('a'), fn('b'))",
            "('', fn('a'), fn('b'), 1, 2, 3)",
            "(T, fn('a'), fn('b'), 1, 2, 3)",
            "('T', fn('a'), go('b'), 1, 2, 3)",
            "('T', fn('a', 'b'), fn('b'), 1, 2, 3)",
            "('T', fn(''), fn('b'), 1, 2, 3)",
            "('T', fn('a'), fn('c'), 1, 2, 3)",
            "['T', fn('a'), fn('b'), 1, 2, 3]",
        ):
            with self.subTest(source=source):
                self.assertIsNone(lex._pair_identity(_expr(source), plants))


class HeaderEncoding(unittest.TestCase):
    def test_layout(self):
        self.assertEqual(lex._encode({}, 0, None), "{}")
        self.assertEqual(lex._encode([], 3, "pairs"), "[]")
        self.assertEqual(lex._encode("é", 0, None), '"\\u00e9"')
        self.assertEqual(
            lex._encode({"pairs": [{"b": 1, "a": "é"}]}, 0, None),
            '{\n  "pairs": [\n    {"a": "\\u00e9", "b": 1}\n  ]\n}',
        )
        self.assertEqual(
            lex._encode({"x": [1, {"y": []}]}, 0, None),
            '{\n  "x": [\n    1,\n    {\n      "y": []\n    }\n  ]\n}',
        )

    def test_depth_600(self):
        for wrap in (lambda v: {"k": v}, lambda v: [v, 1]):
            value = _nested_value(600, wrap)
            with self.subTest(shape=type(wrap(0)).__name__):
                self.assertEqual(json.loads(lex._encode(value, 0, None)), value)


if __name__ == "__main__":
    unittest.main()
