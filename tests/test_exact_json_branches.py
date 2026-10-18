"""Pin the exact-decimal limits and the type edges of ``exact_json``.

Every refusal below is a fail-closed bound that keeps parsing and exact
serialization operationally bounded; the messages are asserted verbatim.
"""

from __future__ import annotations

import sys
import unittest
from fractions import Fraction
from pathlib import Path

TESTS = Path(__file__).resolve().parent
for entry in (TESTS, TESTS.parent / "pipelines"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

import exact_json
from refusal_case_support import RefusalCaseAssertions

_MAX_BITS = (exact_json.MAX_DECIMAL_DIGITS * 3322 // 1000) + 8

_TOKEN_REFUSALS = (
    ("non-string token", 123, "JSON number token exceeds the exact-decimal limit"),
    ("overlong token", "1" * 5000, "JSON number token exceeds the exact-decimal limit"),
    ("scale past the limit", "1.5e-4096", "JSON number scale exceeds the exact-decimal limit"),
    ("exponent past the limit", "1e4097", "JSON number exponent exceeds the exact-decimal limit"),
)

_FRACTION_REFUSALS = (
    (
        "numerator past the bit bound",
        Fraction(2**_MAX_BITS),
        "JSON number numerator exceeds the exact-decimal limit",
    ),
    (
        "denominator past the bit bound",
        Fraction(3, 2**_MAX_BITS),
        "JSON number denominator exceeds the exact-decimal limit",
    ),
    ("non-terminating decimal", Fraction(1, 3), "JSON number has no finite decimal expansion"),
    (
        "expansion past the bit bound",
        Fraction(2**13000 + 1, 2**4000),
        "JSON number expansion exceeds the exact-decimal limit",
    ),
    (
        "decimal places past the limit",
        Fraction(1, 2**4097),
        "JSON number scale exceeds the exact-decimal limit",
    ),
)


class ExactJsonRefusals(RefusalCaseAssertions, unittest.TestCase):
    def test_exact_float_tokens_outside_the_bounds_are_refused(self):
        self.assert_each_refuses(ValueError, exact_json.ExactJSONFloat, _TOKEN_REFUSALS)

    def test_parse_json_integer_refuses_a_non_string_token(self):
        with self.assertRaises(ValueError) as caught:
            exact_json.parse_json_integer(12)
        self.assertEqual(str(caught.exception), "invalid JSON integer syntax")

    def test_fractions_outside_the_bounds_are_refused(self):
        self.assert_each_refuses(
            ValueError, exact_json.json_number_from_fraction, _FRACTION_REFUSALS
        )


class ExactJsonTypeEdges(unittest.TestCase):
    def test_terminating_negative_fraction_renders_an_exact_token(self):
        rendered = exact_json.json_number_from_fraction(Fraction(-5, 4))
        self.assertIsInstance(rendered, exact_json.ExactJSONFloat)
        self.assertEqual(rendered.json_token, "-1.25")

    def test_reduce_rebuilds_from_the_source_token(self):
        original = exact_json.ExactJSONFloat("1.50")
        factory, args = original.__reduce__()
        self.assertEqual(args, ("1.50",))
        restored = factory(*args)
        self.assertIsInstance(restored, exact_json.ExactJSONFloat)
        self.assertEqual(restored.json_token, "1.50")
        self.assertEqual(restored.fraction, Fraction(3, 2))

    def test_exact_fraction_type_dispatch(self):
        cases = (
            ("bool is not a number", True, None),
            ("fraction passes through", Fraction(1, 3), Fraction(1, 3)),
            ("non-finite float", float("inf"), None),
            ("string is not a number", "1", None),
        )
        for label, value, expected in cases:
            with self.subTest(label):
                self.assertEqual(exact_json.exact_fraction(value), expected)


if __name__ == "__main__":
    unittest.main()
