"""Pin the TTF catalog's literal walk and row helpers, including recursion depth.

``_walk_mapping`` recurses through itself alone, one Python frame per nesting
level for lists, dicts and calls and two for tuples (their generator frame),
exactly as before its split; the depth tests below hold it there.
"""

from __future__ import annotations

import ast
import importlib
import sys
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

cat = importlib.import_module("ttf.catalog")
TtfRefusal = importlib.import_module("ttf._contract").TtfRefusal


def _expr(source: str) -> ast.expr:
    return ast.parse(source, mode="eval").body


def _nested(depth: int, wrap) -> ast.expr:
    node: ast.expr = ast.Constant(1)
    for _ in range(depth):
        node = wrap(node)
    return node


def _expected(depth: int, wrap):
    value = 1
    for _ in range(depth):
        value = wrap(value)
    return value


class WalkMapping(unittest.TestCase):
    def walk(self, source: str, consts=None):
        return cat._walk_mapping(_expr(source), consts or {})

    def test_leaves(self):
        self.assertEqual(self.walk("X", {"X": 7}), 7)
        self.assertIsNone(self.walk("Y", {"X": 7}))
        self.assertEqual(self.walk("'s'"), "s")
        self.assertEqual(self.walk("-2.5"), -2.5)
        self.assertIsNone(self.walk("-'s'"))
        self.assertIsNone(self.walk("-X", {"X": 3}))
        self.assertIsNone(self.walk("+3"))
        self.assertIsNone(self.walk("a.b"))
        self.assertIsNone(cat._walk_mapping(None, {}))

    def test_containers(self):
        self.assertEqual(self.walk("[1, (2, -3), X]", {"X": "x"}), [1, (2, -3), "x"])
        self.assertEqual(
            self.walk("{'a': 1, K: 2, 3: 4, 'spikes': 5, 'raster': 6, **rest, 'a': 9}", {"K": "k"}),
            {"a": 9, "k": 2},
        )

    def test_calls_are_recorded_not_evaluated(self):
        self.assertEqual(
            self.walk("R(1, 'x', note=N, **extra)", {"N": "n"}),
            {"_call": "R", "args": [1, "x"], "kwargs": {"note": "n"}},
        )
        self.assertEqual(
            self.walk("obj.make(2)"),
            {"_call": None, "args": [2], "kwargs": {}},
        )


class WalkDepth(unittest.TestCase):
    """The deepest nesting each shape resolved before the split still resolves."""

    def test_lists_dicts_and_calls_resolve_at_depth_600(self):
        shapes = (
            (lambda n: ast.List(elts=[n], ctx=ast.Load()), lambda v: [v]),
            (lambda n: ast.Dict(keys=[ast.Constant("k")], values=[n]), lambda v: {"k": v}),
            (
                lambda n: ast.Call(func=ast.Name("f"), args=[n], keywords=[]),
                lambda v: {"_call": "f", "args": [v], "kwargs": {}},
            ),
        )
        for wrap_node, wrap_value in shapes:
            with self.subTest(shape=wrap_value(0)):
                walked = cat._walk_mapping(_nested(600, wrap_node), {})
                self.assertEqual(walked, _expected(600, wrap_value))

    def test_tuples_resolve_at_depth_400(self):
        walked = cat._walk_mapping(
            _nested(400, lambda n: ast.Tuple(elts=[n], ctx=ast.Load())), {}
        )
        self.assertEqual(walked, _expected(400, lambda v: (v,)))


class Drafts(unittest.TestCase):
    def test_plant_draft_defaults_every_missing_field(self):
        draft = cat._plant_draft("src.py", record_id="ttf-r12-3")
        self.assertEqual(draft["source_round"], 12)
        self.assertIsNone(draft["index"])
        self.assertEqual(draft["sim_or_real"], "designed")
        self.assertEqual(draft["correctness"], "correct")
        self.assertEqual(draft["reward_total"], 0.0)
        self.assertEqual(draft["title"], "")
        self.assertEqual(draft["source_name"], "src.py")
        self.assertEqual(cat._plant_draft("s", source_round=4)["source_round"], 4)
        self.assertIsNone(cat._plant_draft("s", source_round=True)["source_round"])

    def test_rec_dict_reads_nested_blocks_and_falls_back_to_top_level(self):
        rec = {
            "id": "ttf-r02-1",
            "state": {"domain": "d", "sim_or_real": "hil"},
            "proposed_action": "propose",
            "safety_decision": ["not", "a", "dict"],
            "goal": "g",
            "reward_components": {"notes": "total 0.75"},
        }
        draft = cat._from_rec_dict(rec, "src", 2)
        self.assertEqual(
            (draft["domain"], draft["sim_or_real"], draft["proposed_action"], draft["goal"]),
            ("d", "hil", "propose", "g"),
        )
        self.assertEqual((draft["decision"], draft["reward_total"]), ("", 0.75))

    def test_builder_keeps_the_first_string_per_identity_key(self):
        fn = ast.parse(
            "def rec_3():\n"
            "    a = {'id': f'x', 'domain': 1, 9: 'nine', 'other': 'o', **more}\n"
            "    b = {'id': 'ttf-r04-3', 'domain': 'grid', 'goal': 'first'}\n"
            "    c = {'goal': 'second', 'decision': 'REJECT'}\n"
        ).body[0]
        draft = cat._from_builder_fn(fn, "builders", 3)
        self.assertEqual(draft["record_id"], "ttf-r04-3")
        self.assertEqual((draft["domain"], draft["goal"], draft["decision"]), ("grid", "first", "REJECT"))

    def test_builder_without_an_id_string_is_not_a_plant(self):
        fn = ast.parse("def rec_1():\n    return {'id': ID}\n").body[0]
        self.assertIsNone(cat._from_builder_fn(fn, "builders", 1))

    def test_rec_and_builder_drafts_only_match_their_names(self):
        consts: dict = {}
        self.assertIsNone(cat._rec_draft("RECORD", _expr("{'id': 'x'}"), consts, "s"))
        self.assertIsNone(cat._rec_draft("REC_1", _expr("['x']"), consts, "s"))
        with mock.patch.object(cat, "_walk_mapping", return_value=["not", "a", "dict"]):
            self.assertIsNone(cat._rec_draft("REC_1", _expr("{'id': 'x'}"), consts, "s"))
        self.assertIsNone(cat._builder_draft(ast.parse("x = 1").body[0], "s"))
        self.assertIsNone(cat._builder_draft(ast.parse("def build(): pass").body[0], "s"))

    def test_rec_dicts_win_over_builders_and_see_constants_bound_above(self):
        tree = ast.parse(
            "DOMAIN = 'grid'\n"
            "def rec_1():\n    return {'id': 'ttf-r05-1'}\n"
            "REC_2 = {'id': 'ttf-r05-2', 'domain': DOMAIN, 'late': LATE}\n"
            "LATE = 'too late'\n"
        )
        rows = cat._source_rows(tree, "src")
        self.assertEqual([row["record_id"] for row in rows], ["ttf-r05-2"])
        self.assertEqual(rows[0]["domain"], "grid")
        builders_only = ast.parse("def rec_1():\n    return {'id': 'ttf-r05-1'}\n")
        self.assertEqual(
            [row["record_id"] for row in cat._source_rows(builders_only, "src")], ["ttf-r05-1"]
        )

    def test_unparseable_source_is_a_coded_refusal(self):
        with self.assertRaisesRegex(TtfRefusal, "mill source is not parseable") as caught:
            cat.plants_from_source("def broken(:\n", "broken.py")
        self.assertEqual(caught.exception.code, "CATALOG_AST_NOT_A_PLANT")


class RequiredFields(unittest.TestCase):
    def row(self, **changes):
        row = cat.load_catalog().plants[0].as_mapping()
        row.update(changes)
        return row

    def test_vocabulary_fields_refuse_in_field_order(self):
        cases = (
            ({"sim_or_real": "real"}, "sim_or_real must be designed/hil/simulated, got 'real'"),
            ({"decision": "ALLOW"}, "decision must be ACCEPT/MODIFY/REJECT, got 'ALLOW'"),
            ({"correctness": "maybe", "decision": "ALLOW"}, "decision must be"),
            ({"correctness": "maybe"}, "correctness must be correct/incorrect, got 'maybe'"),
        )
        for changes, message in cases:
            with self.subTest(changes=changes), self.assertRaisesRegex(TtfRefusal, message):
                cat.plant_from_mapping(self.row(**changes), "row")

    def test_text_fields_must_be_strings_and_domain_is_required(self):
        with self.assertRaisesRegex(TtfRefusal, r"row\.title must be a string, got 3"):
            cat.plant_from_mapping(self.row(title=3), "row")
        with self.assertRaisesRegex(TtfRefusal, "row needs domain and decision"):
            cat.plant_from_mapping(self.row(domain=""), "row")

    def test_checked_fields_keep_ints_and_float_the_reward(self):
        plant = cat.plant_from_mapping(self.row(reward_total=2), "row")
        self.assertIsInstance(plant.reward_total, float)
        self.assertEqual(plant.reward_total, 2.0)


if __name__ == "__main__":
    unittest.main()
