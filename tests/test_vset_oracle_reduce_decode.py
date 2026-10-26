"""Unit coverage for the reduce decoder the oracle uses to rebuild values."""

from __future__ import annotations

import base64
import sys
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from vset_testutil import PIPELINES  # noqa: E402

import vset_oracle_reduce_decode as dec  # noqa: E402

if not PIPELINES.is_dir():
    raise RuntimeError("pipelines")


class ReduceDecodeTests(unittest.TestCase):
    def test_reduce_decode_walks_plain_trees_and_skips_the_rest(self) -> None:
        self.assertTrue(dec.plain_tree({"a": [1, "x"], "slot": 3}))
        self.assertFalse(dec.plain_tree({"cb": 1}))
        self.assertFalse(dec.plain_tree({"ref": 1}))
        self.assertFalse(dec.plain_tree(object()))
        self.assertFalse(dec.plain_tree([{"cb": 1}]))
        dropped = dec.drop_slots({"a": 1, "slot": 9, "b": [2, {"slot": 3}]})
        self.assertEqual(dropped, {"a": 1, "b": [2, {}]})
        self.assertEqual(dec.drop_slots([{"slot": 1, "n": 2}]), [{"n": 2}])
        self.assertEqual(dec.decode([1]), [1])
        raw = base64.b64encode(b"ab").decode("ascii")
        self.assertEqual(dec.decode({"bytes": raw}), b"ab")
        self.assertEqual(dec.decode({"seq": [1, 2], "tuple": True}), (1, 2))
        self.assertEqual(dec.decode({"seq": [1]}), [1])
        self.assertEqual(dec.decode({"seq": "no"}), [])
        with self.assertRaises(dec._Skip):
            dec.decode({"nope": 1})
        with self.assertRaises(dec._Skip):
            dec.load_qualified(1, "X")
        with self.assertRaises(dec._Skip):
            dec.load_qualified("json", 1)
        with self.assertRaises(dec._Skip):
            dec.load_qualified("not-a-module", "X")
        with self.assertRaises(dec._Skip):
            dec.load_qualified("json", "missing.Name")
        with self.assertRaises(dec._Skip):
            dec.materialize({"reduce": "json"})
        with self.assertRaises(dec._Skip):
            dec.materialize({"reduce": {"m": "json", "q": "dumps"}, "args": "no"})
        made = dec.materialize({"reduce": {"m": "json", "q": "loads"}, "args": ['{"n": 1}']})
        self.assertEqual(made, {"n": 1})

        class Box:
            def __setstate__(self, state: object) -> None:
                self.state = state

        box = Box()
        dec.apply_state(box, {})
        dec.apply_state(box, {"state": [["n", 1]]})
        self.assertEqual(box.state, {"n": 1})
        dec.apply_state(box, {"state": [["k", 2]]})
        self.assertEqual(box.state, {"k": 2})
        plain = type("P", (), {})()
        dec.apply_state(plain, {"state": [["n", 3]]})
        self.assertEqual(plain.n, 3)
        with self.assertRaises(dec._Skip):
            dec.apply_state(plain, {"state": {"n": 1}})
        with self.assertRaises(dec._Skip):
            dec.apply_state(plain, {"state": 1})
