#!/usr/bin/env python3
"""The coded-refusal assertion shared by every family's test support module.

A family's refusal must carry exactly the expected finding code, start with
``"CODE: "``, mention no other finding code and no reason code in its prose,
and contain every fragment the test names. The fault family's
``refusal(case, code, *fragments)`` and the code-repair family's delegate here
so the assertion exists once.
"""

import contextlib
import re
from typing import NamedTuple

_CODE_TOKEN = re.compile(r"[A-Z][A-Z0-9_]+")

__all__ = ("CodedFamily", "coded_refusal", "codes_in")


class CodedFamily(NamedTuple):
    """A family's refusal type with its declared finding and reason codes."""

    refusal_type: type
    finding_codes: frozenset
    reason_codes: frozenset


def codes_in(text, declared):
    """The declared code tokens that appear in ``text``, in order."""

    return [token for token in _CODE_TOKEN.findall(text) if token in declared]


@contextlib.contextmanager
def coded_refusal(case, family, code, *fragments):
    """Assert the family's refusal carrying exactly ``code`` and every prose fragment."""

    with case.assertRaises(family.refusal_type) as caught:
        yield caught
    text = str(caught.exception)
    case.assertEqual(caught.exception.code, code, text)
    case.assertTrue(text.startswith(f"{code}: "), text)
    case.assertEqual(codes_in(text, family.finding_codes), [code], text)
    case.assertEqual(codes_in(text, family.reason_codes), [], text)
    for fragment in fragments:
        case.assertIn(fragment, text)
