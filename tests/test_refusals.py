#!/usr/bin/env python3
"""Coded contract refusals (``pipelines/oracle_grounded/refusals.py``).

The behaviour the fault family pinned for ``FaultRefusal`` now lives in the
shared base, so a second family can declare its own codes without a second
copy of the helpers.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from distill_contract_test_support import REPO, envelope, oc  # noqa: E402
from oracle_grounded import fault_vocabulary as fv, refusals  # noqa: E402


class _Refusal(refusals.CodedRefusal):
    CODES = frozenset({"ONE", "TWO"})


refuse, refuse_when, refuse_first = refusals.helpers(_Refusal)


class CodedRefusalBehaviour(unittest.TestCase):
    def test_a_refusal_is_a_contract_error_with_code_and_prose(self):
        exc = _Refusal("ONE", "the prose")
        self.assertIsInstance(exc, envelope.ContractError)
        self.assertIsInstance(exc, oc.ContractError)
        self.assertEqual(str(exc), "ONE: the prose")
        self.assertEqual((exc.code, exc.message), ("ONE", "the prose"))

    def test_an_undeclared_code_is_a_programming_error(self):
        with self.assertRaises(LookupError):
            _Refusal("THREE", "x")
        with self.assertRaises(LookupError):
            refuse("three", "lowercase is not declared either")
        with self.assertRaises(LookupError):
            refusals.CodedRefusal("ONE", "the base declares nothing")

    def test_the_helpers_are_bound_to_their_type(self):
        with self.assertRaises(_Refusal) as caught:
            refuse("TWO", "direct")
        self.assertEqual(caught.exception.code, "TWO")
        refuse_when(False, "ONE", "not raised")
        with self.assertRaises(_Refusal):
            refuse_when(True, "ONE", "raised")
        refuse_first(((False, "ONE", "a"),))
        with self.assertRaises(_Refusal) as caught:
            refuse_first(((False, "ONE", "skipped"), (True, "TWO", "first"), (True, "ONE", "never")))
        self.assertEqual(caught.exception.code, "TWO")

    def test_shown_prints_a_value_or_its_width(self):
        self.assertEqual(refusals.shown("x"), "'x'")
        self.assertEqual(refusals.shown(10**5000), "an unprintable int of 16610 bits")
        self.assertEqual(refusals.shown([10**5000]), "an unprintable list")

    def test_code_of_reads_the_declared_head_only(self):
        self.assertEqual(refusals.code_of("ONE: prose", _Refusal.CODES), "ONE")
        self.assertIsNone(refusals.code_of("THREE: prose", _Refusal.CODES))
        self.assertIsNone(refusals.code_of("no head here", _Refusal.CODES))
        self.assertIsNone(refusals.code_of(None, _Refusal.CODES))


class FaultFamilyStillWorks(unittest.TestCase):
    def test_fault_refusal_is_a_coded_refusal_with_the_family_codes(self):
        self.assertTrue(issubclass(fv.FaultRefusal, refusals.CodedRefusal))
        self.assertIs(fv.FaultRefusal.CODES, fv.FINDING_CODE_SET)
        self.assertIs(fv.shown, refusals.shown)
        self.assertEqual(fv.finding_code("INPUT_NOT_AN_OBJECT: x"), "INPUT_NOT_AN_OBJECT")
        self.assertIsNone(fv.finding_code("ONE: not a fault code"))


class ImportBinding(unittest.TestCase):
    def test_both_spellings_are_one_object(self):
        if str(REPO) not in sys.path:
            sys.path.append(str(REPO))
        from pipelines.oracle_grounded import refusals as packaged

        self.assertIs(packaged, refusals)
        self.assertIs(packaged.CodedRefusal, refusals.CodedRefusal)


if __name__ == "__main__":
    unittest.main()
