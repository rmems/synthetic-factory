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
    import ipaddress
    from collections import ChainMap, UserDict, UserList, UserString, deque
    class Row(tuple):
        pass
    def text():
        return UserString("alice")
    def udict():
        return UserDict({"a": 1})
    def ulist():
        return UserList([1, 2])
    def chain():
        return ChainMap({"a": 1})
    def addr():
        return ipaddress.ip_address("10.0.0.1")
    def addr6():
        return ipaddress.ip_address("::1")
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
        def test_tables(self):
            import ipaddress
            from collections import ChainMap, UserDict, UserList
            self.assertEqual(c.udict(), {"a": 1})
            self.assertEqual(c.udict(), UserDict({"a": 1}))
            self.assertEqual(c.ulist(), [1, 2])
            self.assertEqual(c.ulist(), UserList([1, 2]))
            self.assertEqual(c.chain(), {"a": 1})
            self.assertEqual(c.chain(), ChainMap({"a": 1}))
            self.assertLess(c.addr(), ipaddress.ip_address("10.0.0.2"))
            self.assertEqual(c.addr6(), ipaddress.ip_address("::1"))
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


_METHODS = textwrap.dedent(
    """\
    from collections import deque
    class Vec(tuple):
        def norm(self):
            return sum(x * x for x in self)
    class Lines(deque):
        def first(self):
            return self[0]
    def vec():
        return Vec((1, 2))
    def lines():
        return Lines(["a", "b"])
    def total(a, b):
        return a + b
    """
)

_METHOD_TESTS = textwrap.indent(
    textwrap.dedent(
        """\
        def test_vec(self):
            self.assertEqual(c.vec().norm(), 5)
            self.assertIsInstance(c.vec(), c.Vec)
            self.assertEqual(c.vec(), (1, 2))
        def test_lines(self):
            self.assertEqual(c.lines().first(), "a")
            self.assertIsInstance(c.lines(), c.Lines)
            self.assertEqual(list(c.lines()), ["a", "b"])
        def test_number(self):
            self.assertEqual(c.total(1, 2), 3)
        """
    ),
    "    ",
)


_FLIP = textwrap.dedent(
    """\
    class Flip:
        n = 0
        def __bool__(self):
            Flip.n += 1
            return Flip.n % 2 == 0
    class Item:
        def __eq__(self, other):
            return Flip()
        def __lt__(self, other):
            return Flip()
        __hash__ = None
    def add(a, b):
        return Item()
    def total(a, b):
        return a + b
    """
)

_FLIP_TESTS = textwrap.indent(
    textwrap.dedent(
        """\
        def test_equal(self):
            self.assertEqual(c.add(2, 2), 5)
            self.assertLess(c.add(2, 2), 5)
        def test_number(self):
            self.assertEqual(c.total(1, 2), 3)
        """
    ),
    "    ",
)

_FLIP_COUNTER = textwrap.dedent(
    """\
    class Flip:
        n = 0
        def __bool__(self):
            Flip.n += 1
            return Flip.n % 2 == 0
    class Item:
        def __eq__(self, other):
            return Flip()
        __hash__ = None
    class Counter:
        def __init__(self, value=0):
            self._value = int(value)
        def add(self, delta):
            if delta is None:
                raise ValueError("delta")
            self._value += int(delta)
            return self._value
        def sub(self, delta):
            return Item()
        def get(self):
            return Item()
    """
)


_ALWAYS_EQ = textwrap.dedent(
    """\
    class Any:
        def __eq__(self, other):
            return True
        __hash__ = None
    def add(a, b):
        return Any()
    def total(a, b):
        return a + b
    """
)

_REBIND = (
    "import __main__\n__main__.user_compares = lambda obj: []\n" + _ALWAYS_EQ
)

_REBIND_FIELDS = (
    "import __main__\n__main__.plain_fields = lambda obj: {'n': 999}\n" + _ALWAYS_EQ
)

_REBIND_NS = (
    "import __main__\n"
    "ns = getattr(__main__, '_NS', None)\n"
    "if isinstance(ns, dict):\n"
    "    ns['user_compares'] = lambda obj: []\n"
    "    ns['plain_fields'] = lambda obj: {'n': 999}\n"
    + _ALWAYS_EQ
)

_REBIND_GC = (
    "import gc, types\n"
    "for item in gc.get_objects():\n"
    "    if not isinstance(item, types.FunctionType):\n"
    "        continue\n"
    "    globs = getattr(item, '__globals__', None)\n"
    "    if not isinstance(globs, dict) or 'user_compares' not in globs:\n"
    "        continue\n"
    "    globs['user_compares'] = lambda obj: []\n"
    "    globs['plain_fields'] = lambda obj: {'n': 999}\n"
    "    globs['object_state'] = lambda obj: {'kind': 'state', 'fields': {}, 'user': []}\n"
    + _ALWAYS_EQ
)

_REBIND_TESTS = textwrap.indent(
    textwrap.dedent(
        """\
        def test_equal(self):
            self.assertEqual(c.add(1, 2), 999)
        def test_number(self):
            self.assertEqual(c.total(1, 2), 3)
        """
    ),
    "    ",
)

_REBIND_COUNTER = (
    "import __main__\n__main__.user_compares = lambda obj: []\n" + _USERLIST
)

_REBIND_SLOT = (
    "import __main__\n__main__._user_compare = lambda name, found: False\n" + _ALWAYS_EQ
)

_REBIND_SLOT_COUNTER = (
    "import __main__\n__main__._user_compare = lambda name, found: False\n" + _USERLIST
)

_REBIND_TRUSTED = textwrap.dedent(
    """\
    import __main__
    def _plant(obj):
        for cls in type(obj).__mro__:
            found = cls.__dict__.get("__eq__")
            if found is None:
                continue
            __main__._TRUSTED[id(found)] = found
            return
    class Any:
        def __eq__(self, other):
            _plant(self)
            return True
        __hash__ = None
    def add(a, b):
        return Any()
    def total(a, b):
        return a + b
    """
)

_FRAME = textwrap.dedent(
    """\
    import sys
    def _grab():
        frame = sys._getframe(0)
        while frame is not None:
            globs = getattr(frame, "f_globals", None)
            if isinstance(globs, dict) and "user_compares" in globs:
                globs["user_compares"] = lambda obj: []
                globs["plain_fields"] = lambda obj: {"n": 999}
            frame = frame.f_back
    class Any:
        def __eq__(self, other):
            _grab()
            return True
        __hash__ = None
    def add(a, b):
        return Any()
    def total(a, b):
        return a + b
    """
)

_DEFAULTS = textwrap.dedent(
    """\
    import gc, types
    def _poke():
        names = {"object_state", "run_op", "handle", "user_compares", "plain_fields"}
        for item in gc.get_objects():
            if not isinstance(item, types.FunctionType):
                continue
            if item.__name__ not in names or item.__defaults__ is None:
                continue
            item.__defaults__ = tuple(lambda *args, **kwargs: [] for _ in item.__defaults__)
    class Any:
        def __eq__(self, other):
            _poke()
            return True
        __hash__ = None
    def add(a, b):
        return Any()
    def total(a, b):
        return a + b
    """
)

_REBIND_NS_COUNTER = (
    "import __main__\n"
    "ns = getattr(__main__, '_NS', None)\n"
    "if isinstance(ns, dict):\n"
    "    ns['user_compares'] = lambda obj: []\n"
    + _USERLIST
)


class StructuralForgeTests(unittest.TestCase):
    def test_worker_rebind_cannot_force_equality(self) -> None:
        _expect_refused(self, _REBIND, _REBIND_TESTS, ("test_equal",))
        _expect_refused(self, _REBIND_FIELDS, _REBIND_TESTS, ("test_equal",))
        _expect_refused(self, _REBIND_NS, _REBIND_TESTS, ("test_equal",))
        _expect_refused(self, _REBIND_GC, _REBIND_TESTS, ("test_equal",))
        _expect_refused(self, _FRAME, _REBIND_TESTS, ("test_equal",))
        _expect_refused(self, _DEFAULTS, _REBIND_TESTS, ("test_equal",))
        self.assertGreater(_error_count(_record(_REBIND_COUNTER)), 0)
        self.assertGreater(_error_count(_record(_REBIND_NS_COUNTER)), 0)

    def test_user_compare_rebind_cannot_force_equality(self) -> None:
        _expect_refused(self, _REBIND_SLOT, _REBIND_TESTS, ("test_equal",))
        _expect_refused(self, _REBIND_TRUSTED, _REBIND_TESTS, ("test_equal",))
        self.assertGreater(_error_count(_record(_REBIND_SLOT_COUNTER)), 0)

    def test_flipping_bool_cannot_force_equality(self) -> None:
        _expect_refused(self, _FLIP, _FLIP_TESTS, ("test_equal",))
        self.assertGreater(_error_count(_record(_FLIP_COUNTER)), 0)

    def test_userlist_record_is_refused(self) -> None:
        self.assertGreater(_error_count(_record(_USERLIST)), 0)

    def test_structural_wrappers_cannot_force_equality(self) -> None:
        _expect_refused(self, _STRUCT, _STRUCT_TESTS, ("test_user", "test_seq"))

    def test_honest_structural_values_compare(self) -> None:
        report, _statuses = _reference(_HONEST, _HONEST_TESTS)
        self.assertTrue(report["reference"]["ok"], report["reference"])

    def test_subclass_methods_stay_on_the_candidate(self) -> None:
        report, _statuses = _reference(_METHODS, _METHOD_TESTS)
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
