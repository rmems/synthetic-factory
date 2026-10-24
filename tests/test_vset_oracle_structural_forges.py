"""Stdlib comparison slots must not be a pass channel for candidate values."""

from __future__ import annotations

import sys
import textwrap
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from test_vset_oracle_inprocess_forges import (  # noqa: E402
    _error_count,
    _expect_refused,
    _record,
    _reference,
)

_USERLIST = textwrap.dedent(
    """\
    from collections import UserList
    class Any:
        def __eq__(self, other):
            return True
        __hash__ = object.__hash__
    class Counter:
        def __init__(self, value=0):
            self._value = int(value)
        def add(self, delta):
            if delta is None:
                raise ValueError("delta")
            self._value += int(delta)
            return self._value
        def sub(self, delta):
            return self._made()
        def get(self):
            return self._made()
        def _made(self):
            found = UserList()
            found.data = Any()
            return found
    """
)

_STRUCT = textwrap.dedent(
    """\
    class Any:
        def __eq__(self, other):
            return True
        def __lt__(self, other):
            return True
        __hash__ = object.__hash__
    def user_list():
        from collections import UserList
        found = UserList()
        found.data = Any()
        return found
    def user_text():
        from collections import UserString
        found = UserString("")
        found.data = Any()
        return found
    def as_tuple():
        class Row(tuple):
            pass
        return Row((Any(),))
    def as_deque():
        from collections import deque
        class Line(deque):
            pass
        return Line([Any()])
    def as_list():
        return [Any()]
    def total(a, b):
        return a + b
    """
)

_STRUCT_TESTS = textwrap.indent(
    textwrap.dedent(
        """\
        def test_user(self):
            self.assertEqual(c.user_list(), "alice")
            self.assertEqual(c.user_text(), "alice")
        def test_seq(self):
            from collections import deque
            self.assertEqual(c.as_tuple(), (999,))
            self.assertEqual(c.as_deque(), deque([999]))
            self.assertLess(c.as_list(), [999])
            self.assertGreater(c.as_list(), [0])
        def test_number(self):
            self.assertEqual(c.total(1, 2), 3)
        """
    ),
    "    ",
)

_HONEST = textwrap.dedent(
    """\
    from collections import UserString, deque
    class Row(tuple):
        pass
    def text():
        return UserString("alice")
    def seq():
        return Row((1, 2))
    def line():
        return deque([1, 2])
    def total(a, b):
        return a + b
    """
)

_HONEST_TESTS = textwrap.indent(
    textwrap.dedent(
        """\
        def test_text(self):
            self.assertEqual(c.text(), "alice")
        def test_seq(self):
            self.assertEqual(c.seq(), (1, 2))
        def test_line(self):
            from collections import deque
            self.assertEqual(c.line(), deque([1, 2]))
            self.assertLess(c.line(), deque([9]))
        def test_number(self):
            self.assertEqual(c.total(1, 2), 3)
        """
    ),
    "    ",
)


class StructuralForgeTests(unittest.TestCase):
    def test_userlist_record_is_refused(self) -> None:
        self.assertGreater(_error_count(_record(_USERLIST)), 0)

    def test_structural_wrappers_cannot_force_equality(self) -> None:
        _expect_refused(self, _STRUCT, _STRUCT_TESTS, ("test_user", "test_seq"))

    def test_honest_structural_values_compare(self) -> None:
        report, _statuses = _reference(_HONEST, _HONEST_TESTS)
        self.assertTrue(report["reference"]["ok"], report["reference"])

    def test_container_wrappers_cannot_force_equality(self) -> None:
        source = textwrap.dedent(
            """\
            class E:
                def __eq__(self, other):
                    return True
                def __hash__(self):
                    return 0
            def wrapped(a, b):
                return [E()]
            def dicted(a, b):
                return {"k": E()}
            def total(a, b):
                return a + b
            """
        )
        tests = textwrap.indent(
            textwrap.dedent(
                """\
                def test_list(self):
                    self.assertEqual(c.wrapped(1, 2), [999])
                    self.assertListEqual(c.wrapped(1, 2), ["no"])
                    self.assertIn(999, c.wrapped(1, 2))
                def test_dict(self):
                    self.assertEqual(c.dicted(1, 2), {"k": "nope"})
                def test_number(self):
                    self.assertEqual(c.total(1, 2), 3)
                """
            ),
            "    ",
        )
        _expect_refused(self, source, tests, ("test_list", "test_dict"))

    def test_reused_slot_identity_cannot_force_equality(self) -> None:
        source = textwrap.dedent(
            """\
            import fractions, types, gc
            _code = fractions.Fraction.__dict__["__eq__"].__code__
            def _make():
                g = {"__builtins__": {"type": lambda x: int, "int": int,
                     "isinstance": lambda *a: False, "NotImplemented": True}}
                old = id(fractions.Fraction.__dict__["__eq__"])
                gc.disable()
                del fractions.Fraction.__eq__
                keep = []
                for _ in range(2000):
                    f = types.FunctionType(_code, g, "__eq__")
                    if id(f) == old:
                        return f
                    keep.append(f)
                return keep[-1]
            class E:
                __hash__ = None
            E.__eq__ = _make()
            def add(a, b):
                return E()
            def total(a, b):
                return a + b
            """
        )
        tests = textwrap.indent(
            textwrap.dedent(
                """\
                def test_equal(self):
                    self.assertEqual(c.add(1, 2), 999)
                def test_number(self):
                    self.assertEqual(c.total(4, 5), 9)
                """
            ),
            "    ",
        )
        _expect_refused(self, source, tests, ("test_equal",))
