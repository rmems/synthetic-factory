"""Branch coverage for tag_regex: the linear-time taxonomy regex subset.

Each refusal is a fail-closed contract: a taxonomy regex outside the subset
raises ``TagTaxonomyError`` naming the source, label and reason.
"""

import re
import sys
import unittest
from pathlib import Path
from re import _parser as re_parser
from unittest import mock

_PIPELINES = Path(__file__).resolve().parents[1] / "pipelines"
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import tag_regex
from tag_constants import TagTaxonomyError
from tag_regex_domain import regex_atom_domain

SUBSET = "is outside the supported linear-time regex subset"


def _parse(pattern):
    return re_parser.parse(pattern, 0)


def _domain(char):
    return regex_atom_domain(_parse(char)[0])


def _compile(pattern):
    return tag_regex.compile_taxonomy_regex(pattern, "tags.demo", "taxonomy.json")


class NullableTests(unittest.TestCase):
    CASES = (
        ("^$", True),
        ("a", False),
        ("(?:)", True),
        ("(a)", False),
        ("(?i:)", False),
        ("(?-i:)", False),
        ("(?:ab|)", True),
        ("ab|cd", False),
        ("a*", True),
        ("(?:a*)+", True),
        ("a+", False),
        ("(?=a)", False),
    )

    def test_sequence_nullability_by_operation(self):
        for pattern, expected in self.CASES:
            with self.subTest(pattern=pattern):
                self.assertIs(tag_regex.regex_sequence_is_nullable(_parse(pattern)), expected)


class LeadingDomainTests(unittest.TestCase):
    def test_provable_leading_domains(self):
        for pattern in ("^a", "(a)", "a+b"):
            with self.subTest(pattern=pattern):
                self.assertEqual(tag_regex.regex_leading_domain(_parse(pattern)), _domain("a"))

    def test_unprovable_leading_domains_are_none(self):
        for pattern in ("(?i:a)", "(?-i:a)", "ab|cd", "a*b", "(?=a)", "^"):
            with self.subTest(pattern=pattern):
                self.assertIsNone(tag_regex.regex_leading_domain(_parse(pattern)))

    def test_append_regex_domain_deduplicates(self):
        domains = []
        tag_regex.append_regex_domain(domains, _domain("a"))
        tag_regex.append_regex_domain(domains, _domain("a"))
        self.assertEqual(domains, [_domain("a")])

    def test_safe_repeat_boundary_needs_a_disjoint_consuming_atom(self):
        cases = (("^", False), ("^a", False), ("^b", True))
        for between, expected in cases:
            with self.subTest(between=between):
                result = tag_regex.has_safe_repeat_boundary(_domain("a"), _parse(between))
                self.assertIs(result, expected)


class SubsetRefusalTests(unittest.TestCase):
    CASES = (
        ("(?=a)", "unsupported regex operation"),
        ("(?i:a)", "inline flags are not supported"),
        ("(?-i:a)", "inline flags are not supported"),
        ("(?i)a", "inline flags are not supported"),
        ("a*(?:bc|de)", "a variable repeat may not be followed by alternation"),
        ("a{2}" * 65, "too many repeat operations"),
        ("a{10001}", "repeat upper bound exceeds 10000"),
        ("(?:ab)*", "a repeat above one may cover only one consuming atom"),
        ("a*a*", "adjacent variable repeats have overlapping character domains"),
        ("a*a{2}", "a variable repeat overlaps its following fixed repeat"),
        ("a*a", "a variable repeat overlaps its following token"),
        ("a+b+", "unbounded repeats lack a deterministic boundary"),
        ("(?:a*b|cd)", "alternation branches need disjoint leading domains"),
        ("(?:ab|[a-c]d)", "alternation branches need disjoint leading domains"),
    )

    def test_each_unsafe_construct_is_refused_with_its_reason(self):
        for pattern, reason in self.CASES:
            with self.subTest(pattern=pattern[:20]):
                with self.assertRaises(TagTaxonomyError) as caught:
                    _compile(pattern)
                message = str(caught.exception)
                self.assertTrue(message.startswith(f"taxonomy.json: tags.demo {SUBSET}"))
                self.assertIn(reason, message)

    def test_too_many_alternation_branches(self):
        chars = [chr(code) for code in range(0x100, 0x100 + 65)]
        pattern = "(?:" + "|".join(f"{char}0" for char in chars) + ")"
        with self.assertRaisesRegex(TagTaxonomyError, "too many alternation branches"):
            _compile(pattern)

    def test_overlong_pattern_is_refused_before_parsing(self):
        with (
            mock.patch.object(tag_regex, "_parse_taxonomy_pattern") as parse,
            self.assertRaisesRegex(TagTaxonomyError, "pattern exceeds 8192 characters"),
        ):
            _compile("a" * 8193)
        parse.assert_not_called()


class SubsetAcceptanceTests(unittest.TestCase):
    PATTERNS = (
        "a*a{0}",
        "(?:ab*)?c",
        "(?:ab*|cd)e",
        "a+-b+",
    )

    def test_linear_patterns_compile(self):
        for pattern in self.PATTERNS:
            with self.subTest(pattern=pattern):
                self.assertEqual(_compile(pattern).pattern, pattern)


class ResourceFailureTests(unittest.TestCase):
    def test_validator_resource_error_is_reported_as_invalid_regex(self):
        target = "validate_linear_regex_sequence"
        with (
            mock.patch.object(tag_regex, target, side_effect=RecursionError),
            self.assertRaisesRegex(TagTaxonomyError, "validator resource limit exceeded"),
        ):
            _compile("abc")

    def test_compiler_re_error_is_reported_as_invalid_regex(self):
        boom = re.error("boom")
        with (
            self.assertRaises(TagTaxonomyError) as caught,
            mock.patch.object(tag_regex.re, "compile", side_effect=boom),
        ):
            _compile("abc")
        expected = "taxonomy.json: tags.demo is not a valid regex: boom"
        self.assertEqual(str(caught.exception), expected)


if __name__ == "__main__":
    unittest.main()
