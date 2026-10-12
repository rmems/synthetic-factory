#!/usr/bin/env python3
"""NTP AST literal, call and path helpers on small snippets."""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from ntp import catalog_ast  # noqa: E402


class NtpCatalogAstTests(unittest.TestCase):
    @staticmethod
    def expr(source: str) -> ast.AST:
        return ast.parse(source, mode="eval").body

    def test_literal_value_operators_and_containers(self):
        env = {"A": "dagster", "N": 2}
        unset = catalog_ast.UNSET
        cases = (
            ("A", "dagster"),
            ("MISSING", unset),
            ("f'{A}-{N}'", "dagster-2"),
            ("f'{MISSING}'", unset),
            ("f'{1.5}'", unset),
            ("-N", -2),
            ("-A", unset),
            ("not N", unset),
            ("A + '-leftover'", "dagster-leftover"),
            ("A + N", unset),
            ("N * 2", unset),
            ("{A: N}", {"dagster": 2}),
            ("{**A}", unset),
            ("{A: MISSING}", unset),
            ("{A, 'x'}", {"dagster", "x"}),
            ("{MISSING}", unset),
            ("A.upper()", unset),
        )
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(catalog_ast.literal_value(self.expr(source), env), expected)

    def test_call_kwargs_needs_literal_keywords_only(self):
        env = {"STEM": "kfp"}
        cases = (
            ("S(slug='a', stem=STEM)", {"slug": "a", "stem": "kfp"}),
            ("S('a', slug='b')", None),
            ("S(**ROW)", None),
            ("S(slug=MISSING)", None),
            ("obj.S(slug='a')", None),
            ("'not a call'", None),
        )
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(catalog_ast.call_kwargs(self.expr(source), env), expected)

    def test_joined_path_constant_shapes(self):
        cases = (
            ("'experiments/x.py'", "experiments/x.py"),
            ("str(ROOT / 'experiments' / 'x.py')", "experiments/x.py"),
            ("ROOT", None),
            ("ROOT / NAME", None),
            ("ROOT / 'x.py'", "x.py"),
            ("'a' - 'b'", None),
            ("ROOT.parent", None),
        )
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(catalog_ast.joined_path_constant(self.expr(source)), expected)

    def test_write_wave_ignores_non_name_callees(self):
        self.assertIsNone(catalog_ast.extract_write_wave_mill("fns[0](3)\nwrite_wave(NAME)\n"))
        self.assertEqual(
            catalog_ast.extract_write_wave_mill("fns[0](3)\ng.write_wave(7, rows)\n"),
            "experiments/ntp-mill-unique-llll7.py",
        )


if __name__ == "__main__":
    unittest.main()
