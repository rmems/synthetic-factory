"""Parent-side branches the subprocess suite does not reach."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from vset_testutil import PIPELINES  # noqa: E402

import vset_oracle_compare as cmp  # noqa: E402
import vset_oracle_reduce as red  # noqa: E402
import vset_oracle_status as labels  # noqa: E402

if not PIPELINES.is_dir():
    raise RuntimeError("pipelines")


class _Boom:
    def __eq__(self, other: object) -> bool:
        raise RuntimeError("eq")


class _Client:
    def __init__(self, found: object) -> None:
        self.found = found

    def exchange(self, _payload: dict[str, object]) -> object:
        if self.found is Ellipsis:
            raise RuntimeError("down")
        return self.found


class _Obj:
    def __init__(self, found: object) -> None:
        self.client = _Client(found)
        self.oid = 1


class _Sample:
    """Stand-in case. A real TestCase would be collected as an empty test."""


def _plain(value: object) -> object:
    if isinstance(value, type):
        return value
    return value


class ParentEdgeTests(unittest.TestCase):
    def test_preview_closes_a_bad_state_read(self) -> None:
        self.assertIsNone(cmp.preview(_Obj({}), "__len__"))
        self.assertEqual(cmp.preview(_Obj(Ellipsis), "__eq__"), {"fields": {}, "user": ["__eq__"]})
        self.assertEqual(cmp.preview(_Obj(["nope"]), "__eq__")["user"], ["__eq__"])
        self.assertFalse(cmp._affirms(NotImplemented))
        self.assertFalse(cmp._same(_Boom(), 1))

    def test_agreement_rejects_a_true_answer_without_fields(self) -> None:
        info = {"fields": {"n": 1, "label": "usd"}, "user": []}
        self.assertIs(cmp.decide("__eq__", NotImplemented, info, 1), NotImplemented)
        self.assertIs(cmp.decide("__iter__", True, None, None), True)
        self.assertIs(cmp.decide("__eq__", True, info, 1), True)
        self.assertIs(cmp.decide("__ne__", True, info, 1), NotImplemented)
        self.assertIs(cmp.decide("__eq__", False, info, 1), False)
        ordered = {"fields": {"n": 0, "label": "usd"}, "user": []}
        self.assertIs(cmp.decide("__lt__", True, ordered, 1), True)
        self.assertFalse(cmp._equal_data({}, 1))
        self.assertFalse(cmp._ordered("__lt__", {}, 1))
        self.assertIs(cmp.decide("__eq__", True, {"fields": {"n": _Boom()}, "user": []}, _Boom()), NotImplemented)
        self.assertIs(cmp.decide("__eq__", True, {"fields": {"label": "ab"}, "user": []}, ("ab",)), True)
        self.assertIs(cmp.decide("__eq__", True, {"fields": {"flag": True}, "user": []}, True), True)
        self.assertIs(cmp.decide("__lt__", True, {"fields": {"n": 5}, "user": []}, 1), NotImplemented)
        self.assertIs(cmp.decide("__eq__", True, None, 1), True)

    def test_user_contains_and_bad_field_reports_are_refused(self) -> None:
        contained = {"fields": {}, "user": ["__contains__"]}
        self.assertIs(cmp.decide("__contains__", True, contained, 1), NotImplemented)
        self.assertIs(cmp.decide("__contains__", True, {"fields": {}, "user": "no"}, 1), NotImplemented)
        self.assertIs(cmp.decide("__contains__", True, {"user": ["__eq__"]}, 1), NotImplemented)
        self.assertIs(cmp.decide("__eq__", True, {"fields": "no", "user": []}, 1), NotImplemented)

    def test_reduce_refuses_shapes_it_cannot_rebuild(self) -> None:
        self.assertFalse(red._known_module(None))
        self.assertFalse(red._known_module(""))

        named = _Boom()
        named.__module__ = "json"  # type: ignore[attr-defined]
        named.__qualname__ = None  # type: ignore[attr-defined]
        with self.assertRaises(red._Skip):
            red._ref(named)

        class Local:
            pass

        with self.assertRaises(red._Skip):
            red._class_arg(Local)
        with self.assertRaises(red._Skip):
            red._arg(1, lambda _value: {"cb": 1})
        self.assertIsNone(red._span("x"))
        self.assertIsNone(red._span((1,)))
        self.assertIsNone(red._span((1, 2, 3, 4, 5, 6)))
        with self.assertRaises(red._Skip):
            red._parts((str, ("a",), None, 1))
        with self.assertRaises(red._Skip):
            red._parts((str, "a"))
        with self.assertRaises(red._Skip):
            red._parts((1,))
        self.assertFalse(red._same(1, {"reduce": {"m": "json", "q": "dumps"}}))
        self.assertEqual(red._state_payload({"a": 1}, _plain), [["a", 1]])
        self.assertEqual(red._state_payload(3, _plain), 3)

        class NoCall:
            __module__ = "json"
            __reduce_ex__ = "nope"

        self.assertIsNone(red._reducer(NoCall()))

        class Drift:
            __module__ = "json"

            def __reduce_ex__(self, _protocol: int) -> object:
                return (json.dumps, ("{}",))

        self.assertIsNone(red.reduce_payload(Drift(), _plain))

    def test_status_reads_errors_fixtures_and_unrun_rows(self) -> None:
        result = unittest.TestResult()
        result.errors.append((None, "e"))  # type: ignore[arg-type]
        self.assertEqual(labels.status(result), "ERROR")
        case = _Sample()
        owned = unittest.TestResult()
        owned.errors.append(case)  # type: ignore[arg-type]
        self.assertEqual(labels.case_status(owned, case), "ERROR")
        holder = unittest.FunctionTestCase(lambda: None)
        holder.description = f"setUpClass ({_Sample.__module__}.{_Sample.__qualname__})"  # type: ignore[attr-defined]
        klass = unittest.TestResult()
        klass.errors.append((holder, "e"))  # type: ignore[arg-type]
        self.assertEqual(labels.case_status(klass, case), "ERROR")
        module = unittest.FunctionTestCase(lambda: None)
        module.description = f"setUpModule ({_Sample.__module__})"  # type: ignore[attr-defined]
        setup = unittest.TestResult()
        setup.failures.append((module, "f"))  # type: ignore[arg-type]
        self.assertEqual(labels.case_status(setup, case), "FAIL")
        down = unittest.FunctionTestCase(lambda: None)
        down.description = "tearDownModule (nope)"  # type: ignore[attr-defined]
        torn = unittest.TestResult()
        torn.testsRun = 1
        torn.errors.append((down, "e"))  # type: ignore[arg-type]
        self.assertEqual(labels.case_status(torn, case), "ok")
        blank = unittest.FunctionTestCase(lambda: None)
        blank.description = 5  # type: ignore[attr-defined]
        weird = unittest.TestResult()
        weird.testsRun = 1
        weird.errors.append((blank, "e"))  # type: ignore[arg-type]
        self.assertEqual(labels.case_status(weird, case), "ok")
        other = unittest.FunctionTestCase(lambda: None)
        unrun = unittest.TestResult()
        unrun.errors.append((other, "e"))  # type: ignore[arg-type]
        self.assertEqual(labels.case_status(unrun, case), "ERROR")
        failed = unittest.TestResult()
        failed.failures.append((other, "f"))  # type: ignore[arg-type]
        self.assertEqual(labels.case_status(failed, case), "FAIL")
        quiet = unittest.TestResult()
        self.assertEqual(labels.case_status(quiet, case), "ok")
