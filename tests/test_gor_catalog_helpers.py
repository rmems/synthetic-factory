"""Pin the GOR literal evaluator, pair-list extract and catalog binders.

``literal_value`` keeps its recursion shape: unary minus and ``+`` recurse
directly (one frame per level) and containers and f-strings through one helper
(two frames per level). The depth tests hold each path at the nesting it
resolved before the split.
"""

from __future__ import annotations

import ast
import importlib
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

gast = importlib.import_module("gor.catalog_ast")
gex = importlib.import_module("gor.catalog_extract")
gcat = importlib.import_module("gor.catalog")
cv = importlib.import_module("gor.vocabulary")
MillSource = importlib.import_module("gor.sources").MillSource
UNSET = gast.UNSET


def _expr(source: str) -> ast.expr:
    return ast.parse(source, mode="eval").body


def _nested(depth: int, wrap, leaf: ast.expr) -> ast.expr:
    node = leaf
    for _ in range(depth):
        node = wrap(node)
    return node


class LiteralValue(unittest.TestCase):
    def value(self, source: str, env=None):
        return gast.literal_value(_expr(source), env)

    def test_leaves_and_operators(self):
        self.assertEqual(self.value("'s'"), "s")
        self.assertEqual(self.value("X", {"X": 4}), 4)
        self.assertIs(self.value("Y", {"X": 4}), UNSET)
        self.assertEqual(self.value("-X", {"X": 4}), -4)
        self.assertIs(self.value("-'s'"), UNSET)
        self.assertEqual(self.value("'a' + X", {"X": "b"}), "ab")
        self.assertIs(self.value("'a' + 1"), UNSET)
        self.assertIs(self.value("a.b"), UNSET)

    def test_containers_and_f_strings(self):
        self.assertEqual(self.value("(1, [2, {3}], {'k': X})", {"X": "x"}), (1, [2, {3}], {"k": "x"}))
        self.assertIs(self.value("[1, Y]"), UNSET)
        self.assertIs(self.value("{'k': 1, **rest}"), UNSET)
        self.assertIs(self.value("{'k': Y}"), UNSET)
        self.assertEqual(self.value("f'r{N}-{S}'", {"N": 946, "S": "x"}), "r946-x")
        self.assertIs(self.value("f'{N}'", {"N": 1.5}), UNSET)
        self.assertIs(self.value("f'{N!r}'"), UNSET)

    def test_depth_600_for_unary_minus_and_concatenation(self):
        neg = _nested(600, lambda n: ast.UnaryOp(op=ast.USub(), operand=n), ast.Constant(1))
        self.assertEqual(gast.literal_value(neg), 1)
        add = _nested(
            600, lambda n: ast.BinOp(left=n, op=ast.Add(), right=ast.Constant("b")), ast.Constant("a")
        )
        self.assertEqual(gast.literal_value(add), "a" + "b" * 600)

    def test_parsed_600_deep_minus_and_plus_chains_resolve_as_module_constants(self):
        source = (
            "CATALOG_FIRST = " + "-" * 600 + "946\n"
            "GEN = " + " + ".join(['"g"'] * 600) + "\n"
            "PAIRS = [({'slug': 'a'}, {'slug': 'b'})]\n"
        )
        extracted = gex.extract_mill_catalog(source, path="experiments/gor-mill-r946.py")
        self.assertEqual((extracted["catalog_first"], extracted["generator"]), (946, "g" * 600))

    def test_depth_400_for_containers_and_f_strings(self):
        shapes = {
            "list": (lambda n: ast.List(elts=[n], ctx=ast.Load()), list),
            "tuple": (lambda n: ast.Tuple(elts=[n], ctx=ast.Load()), tuple),
            "dict": (lambda n: ast.Dict(keys=[ast.Constant("k")], values=[n]), dict),
        }
        for name, (wrap, kind) in shapes.items():
            with self.subTest(shape=name):
                value = gast.literal_value(_nested(400, wrap, ast.Constant(1)))
                for _ in range(400):
                    self.assertIsInstance(value, kind)
                    value = value["k"] if kind is dict else value[0]
                self.assertEqual(value, 1)
        fstring = _nested(
            400,
            lambda n: ast.JoinedStr(values=[ast.FormattedValue(value=n, conversion=-1)]),
            ast.Constant("x"),
        )
        self.assertEqual(gast.literal_value(fstring), "x")


class ConstructorArguments(unittest.TestCase):
    def kwargs(self, source: str, env=None):
        return gast.ctor_kwargs(_expr(source), env)

    def test_positional_names_come_from_the_constructor_table(self):
        names = cv.CTOR_POSARGS["_cfg"]
        self.assertEqual(
            self.kwargs("_cfg('slug-a', 'stem-a', marker=M)", {"M": "m"}),
            {names[0]: "slug-a", names[1]: "stem-a", "marker": "m"},
        )
        self.assertEqual(self.kwargs("_cfg('first', slug='second')")["slug"], "second")
        self.assertEqual(self.kwargs("anything(slug='s')"), {"slug": "s"})

    def test_non_literal_or_unpacking_calls_have_no_arguments(self):
        too_many = "_cfg(" + ", ".join("'x'" for _ in range(len(cv.CTOR_POSARGS["_cfg"]) + 1)) + ")"
        for source in (
            "'not a call'", "obj.plant(slug='s')", "plant(*args)", "plant(**spec)",
            "unknown('positional')", too_many, "plant(slug=SLUG)",
        ):
            with self.subTest(source=source):
                self.assertIsNone(self.kwargs(source))


class JoinedPath(unittest.TestCase):
    def test_root_names_drop_out_and_non_literal_tails_void_the_path(self):
        cases = {
            "ROOT / 'experiments' / 'gor-mill-r946.py'": "experiments/gor-mill-r946.py",
            "'experiments' / 'x.py'": "experiments/x.py",
            "'x.py'": "x.py",
            "ROOT": None,
            "'experiments' / NAME": None,
            "7": None,
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(gast.joined_path_constant(_expr(source)), expected)

    def test_depth_600(self):
        left = _nested(
            600, lambda n: ast.BinOp(left=n, op=ast.Div(), right=ast.Constant("b")), ast.Constant("a")
        )
        self.assertEqual(gast.joined_path_constant(left), "a" + "/b" * 600)


class ListedPairs(unittest.TestCase):
    def listed(self, source: str):
        return gex._listed_pairs(ast.parse(source))

    def test_counts_new_and_more_rows(self):
        record = self.listed(
            "PAIRS = [({'slug': 'a'}, {'slug': 'b'})]\n"
            "NEW_PAIRS = [({'slug': 'c'}, {'slug': 'd'}), ({'slug': 'e'}, {'slug': 'f'})]\n"
            "MORE = [({'slug': 'g'}, {'slug': 'h'})]\n"
            "MORE_PAIRS = []\nOTHER = [1]\nPAIRS_TOO: list = []\n"
        )
        self.assertEqual((record["shape"], record["n_rows"]), (cv.SHAPE_LITERAL, 4))
        self.assertEqual((record["n_new"], record["n_more"]), (2, 1))
        self.assertEqual((record["first_slug"], record["last_slug"]), ("a", "g"))

    def test_plain_pairs_omit_the_counts_and_bad_lists_void_the_extract(self):
        record = self.listed("PAIRS = [(plant(slug='a'), plant(slug='b'))]\n")
        self.assertEqual(record["shape"], cv.SHAPE_PLANT)
        self.assertNotIn("n_new", record)
        self.assertIsNone(self.listed("PAIRS = [1]\n"))
        self.assertIsNone(self.listed("PAIRS = [(mk(slug='a'), mk(slug='b'))]\n"))
        self.assertIsNone(self.listed("x = 1\n"))

    def test_merged_shape(self):
        plant, leftover = cv.SHAPE_PLANT, cv.SHAPE_LEFTOVER_PLANT
        self.assertEqual(gex._merged_shape(None, plant), plant)
        self.assertEqual(gex._merged_shape(plant, plant), plant)
        self.assertEqual(gex._merged_shape(leftover, plant), leftover)
        self.assertEqual(gex._merged_shape(plant, leftover), plant)
        self.assertEqual(gex._merged_shape(plant, cv.SHAPE_GITCFG), cv.SHAPE_GITCFG)
        # Only a shape spelled exactly "leftover" takes this branch; none of the
        # pairs-* shape names do, so a mixed list takes the later shape.
        self.assertEqual(gex._merged_shape("leftover", cv.SHAPE_ADD), leftover)


class AddedPairs(unittest.TestCase):
    def test_add_constructors(self):
        tree = ast.parse("add(_S(slug='a'), _S(slug='b'))\nadd(_S(slug='c'), _S(slug='d'))\nprint(1)\n")
        record = gex._add_pairs(tree)
        self.assertEqual((record["shape"], record["n_rows"]), (cv.SHAPE_ADD, 2))
        for source in ("add(_S(slug='a'))\n", "add(*specs)\n", "x = add\n", "add(_S(slug='a'), _S())\n"):
            with self.subTest(source=source):
                self.assertIsNone(gex._add_pairs(ast.parse(source)))

    def test_pair_identity_forms(self):
        self.assertEqual(
            gex._pair_identity(_expr("_pair(plant(slug='a'), plant(slug='b', handoff=True))"))["fail_handoff"],
            True,
        )
        self.assertEqual(gex._pair_identity(_expr("({'slug': 'a'}, {'slug': 'b'})"))["fail_slug"], "b")
        self.assertIsNone(gex._pair_identity(_expr("_pair(plant(slug='a'))")))
        self.assertIsNone(gex._pair_identity(_expr("[1, 2]")))

    def test_shape_for_element(self):
        cases = {
            "_pair()": None,
            "_pair(*specs)": None,
            "_pair(gitcfg(), x)": cv.SHAPE_GITCFG,
            "_pair(_cmd(), x)": cv.SHAPE_LEFTOVER_PLANT,
            "_pair(plant(), x)": cv.SHAPE_PLANT,
            "_pair(other(), x)": cv.SHAPE_ADD,
            "_pair(spec, x)": cv.SHAPE_ADD,
            "({}, {})": cv.SHAPE_LITERAL,
            "(_S(), _H())": cv.SHAPE_S_H,
            "(leftover_plant(), x)": cv.SHAPE_LEFTOVER_PLANT,
            "(_cfg(), x)": cv.SHAPE_GITCFG,
            "(mk(), x)": None,
            "(a, b, c)": None,
            "[a, b]": None,
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(gex._shape_for_element(_expr(source)), expected)


class PairRows(unittest.TestCase):
    def test_loader_refuses_malformed_lines(self):
        good = gex.dumps_pairs_jsonl([dict.fromkeys(cv.PAIR_ROW_KEYS, 0)])
        cases = {
            "framing": ("{}", "must be LF-framed jsonl"),
            "empty": ("", "must be LF-framed jsonl"),
            "blank": (good + "\n", r"rows\.jsonl:2 is empty"),
            "indent": (" " + good, r"rows\.jsonl:1 is not compact"),
            "json": ("{\n", r"rows\.jsonl:1 is not JSON: "),
            "keys": ('{"a": 1}\n', r"rows\.jsonl:1 keys differ"),
            "list": ("[1]\n", r"rows\.jsonl:1 keys differ"),
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rows.jsonl"
            self.assertEqual(len(self.load(path, good)), 1)
            for name, (text, message) in cases.items():
                with self.subTest(case=name), self.assertRaisesRegex(ValueError, message):
                    self.load(path, text)
            with self.assertRaisesRegex(ValueError, "cannot load GOR pairs"):
                gex.load_pair_rows(Path(tmp) / "missing.jsonl")

    @staticmethod
    def load(path: Path, text: str):
        path.write_text(text, encoding="utf-8", newline="")
        return gex.load_pair_rows(path)


class CatalogBinders(unittest.TestCase):
    def setUp(self):
        self.slice = gcat.CATALOG.mills[cv.SLICE_MILL_ID]
        self.deferred = gcat.CATALOG.mills[cv.BULKY_MILL_ID]

    def test_header_pins(self):
        source = MillSource(self.deferred.mill_id, self.deferred.path, self.deferred.blob_sha, "mill")
        gcat._bind_mill_pin(self.deferred.mill_id, replace(self.deferred, pairs=()), source)
        for changed, message in (
            (replace(self.deferred, path="moved.py", pairs=()), "pin disagrees with sources.py"),
            (replace(self.deferred, blob_sha="0", pairs=()), "pin disagrees with sources.py"),
            (self.deferred, "is not the first slice and must omit pair rows"),
        ):
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                gcat._bind_mill_pin(self.deferred.mill_id, changed, source)
        slice_source = MillSource(self.slice.mill_id, self.slice.path, self.slice.blob_sha, "mill")
        gcat._bind_mill_pin(self.slice.mill_id, self.slice, slice_source)

    def test_deferred_rows(self):
        rows = [{"i": 0, "path": self.deferred.path}, {"i": 1, "path": self.deferred.path}]
        gcat._bind_deferred_rows("m", self.deferred, rows)
        with self.assertRaisesRegex(ValueError, "m pair index drifted"):
            gcat._bind_deferred_rows("m", self.deferred, list(reversed(rows)))
        with self.assertRaisesRegex(ValueError, "m path drifted from catalog"):
            gcat._bind_deferred_rows("m", self.deferred, [{"i": 0, "path": "x.py"}])

    def test_pair_identities(self):
        gcat._bind_pair_identities("m", self.deferred)
        for changed, message in (
            (replace(self.deferred, n_rows=1), "m n_rows does not match committed pair identities"),
            (replace(self.deferred, first_slug="zz"), "m first_slug drifted from pair identities"),
            (replace(self.deferred, last_slug="zz"), "m last_slug drifted from pair identities"),
        ):
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                gcat._bind_pair_identities("m", changed)


if __name__ == "__main__":
    unittest.main()
