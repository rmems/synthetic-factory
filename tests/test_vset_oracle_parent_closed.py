"""Closed subclass paths that never start a candidate child.

Split out of test_vset_oracle_parent so that module stays one responsibility.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parents[1] / "pipelines"
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import vset_oracle_collect as collect  # noqa: E402
import vset_oracle_subclass as subclass  # noqa: E402
import vset_oracle_subclass_call as subclass_call  # noqa: E402


def _tools():
    return subclass, subclass_call, collect


class ParentClosedTests(unittest.TestCase):
    def test_collection_keeps_suites_that_subclass_a_candidate(self) -> None:
        _subclass, _call, collect = _tools()
        source = (
            "import unittest\n"
            "import shapes\n"
            "class Square(shapes.Base):\n"
            "    pass\n"
            "class T(unittest.TestCase):\n"
            "    def test_listed(self):\n"
            "        self.assertTrue(True)\n"
        )
        spec = {"module": "vset_oracle_tests_sub", "relative": "tests/sub.py", "source": source}
        collect.require_match(
            spec,
            ["vset_oracle_tests_sub.T.test_listed"],
            {"sub.py": source},
        )


    def test_subclass_fallbacks_stay_closed(self) -> None:
        subclass, subclass_call, _collect = _tools()
        class Slot:
            __slots__ = ()

        class Plain:
            def area(self):
                return 1

        class Marked:
            _vset_child = 1

        class Busy:
            _vset_adopting = True

        class Held:
            _vset_child = 3

        class Kid(Held):
            pass

        slot = Slot()
        self.assertIsNone(subclass_call._state(slot))
        subclass.mark_ready(1)
        self.assertTrue(subclass_call._ready(slot))
        self.assertFalse(subclass_call._bound(slot))
        self.assertEqual(subclass._encoded(None), [])
        self.assertEqual(subclass._encoded_map(None), {})
        self.assertIs(subclass_call._view(Plain, slot), slot)
        self.assertIs(subclass_call._resolve(Plain, slot), slot)
        made = subclass.spawn(Plain, (), {})
        self.assertIsInstance(made, Plain)
        subclass.adopt(Plain)
        subclass.adopt(Marked)
        subclass.adopt(Busy)
        subclass.adopt(Kid)
        with self.assertRaises(TypeError):
            subclass.spawn(type("Num", (int,), {}), (), {})


    def test_unbound_subclass_uses_the_candidate_constructor(self) -> None:
        subclass, subclass_call, _collect = _tools()
        class Plain:
            def area(self):
                return 1

        child = Plain()
        child.client = None
        child.oid = "x"
        view = subclass_call._resolve(Plain, child)
        self.assertIsInstance(view, Plain)
        self.assertTrue(subclass_call._ready(view))
        dispatch = subclass_call.dispatcher(Plain)
        self.assertEqual(dispatch("area", child, None, None), 1)
        child.oid = 5
        subclass_call._LIVE[(id(None), 5)] = "other"
        self.assertIsInstance(subclass_call._resolve(Plain, child), Plain)

        class Caller:
            def call(self, oid, args, kwargs):
                self.got = (oid, args, kwargs)
                return type("Remote", (), {"oid": 11})()

        caller = Caller()

        class Remote:
            _vset_oid = 8
            _vset_client = caller

        class Num(Remote, int):
            pass

        self.assertEqual(subclass.spawn(Num, (1,), {"k": 2}).oid, 11)
        self.assertEqual(caller.got[0], 8)
        box = object.__new__(type("Box", (Remote,), {}))
        subclass.initialize(box, (2,), {})
        self.assertEqual(box.oid, 11)
        self.assertTrue(subclass_call._ready(box))
        subclass.initialize(Plain(), (), {})
        subclass.clear_live()

