#!/usr/bin/env python3
"""SSR AST helpers, extract fall-throughs and inherited scanners on small snippets."""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from ssr.catalog_extract import (  # noqa: E402
    SHAPE_PLANT,
    SHAPE_TAILS,
    apply_inherited_scanners,
    deferred_pair_rows,
    extract_companion_path,
    extract_mill_catalog,
)
from ssr import catalog_ast, vocabulary as cv  # noqa: E402


class SsrCatalogAstTests(unittest.TestCase):
    @staticmethod
    def expr(source: str) -> ast.AST:
        return ast.parse(source, mode="eval").body

    def test_literal_value_resolves_names_and_expressions(self):
        env = {"A": "gitleaks", "N": 3}
        unset = catalog_ast.UNSET
        cases = (
            ("A", "gitleaks"),
            ("MISSING", unset),
            ("-N", -3),
            ("-2.5", -2.5),
            ("-A", unset),
            ("+N", unset),
            ("A + '-tail'", "gitleaks-tail"),
            ("A + N", unset),
            ("N - 1", unset),
            ("f'{A}-{N}'", "gitleaks-3"),
            ("f'{A!r}'", "gitleaks"),
            ("f'{MISSING}'", unset),
            ("f'{1.5}'", unset),
            ("{A, 'x'}", {"gitleaks", "x"}),
            ("{MISSING}", unset),
            ("{**A}", unset),
            ("{A: MISSING}", unset),
            ("[A, (N, 'x')]", ["gitleaks", (3, "x")]),
            ("A.upper()", unset),
        )
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(catalog_ast.literal_value(self.expr(source), env), expected)

    def test_ctor_identity_reads_keywords_and_s_positionals(self):
        cases = (
            ("plant(slug='a', scanner='gitleaks')", {"slug": "a", "scanner": "gitleaks"}),
            ("plant(scanner='gitleaks')", None),
            ("plant(slug=NAME)", None),
            ("S('a', 'gitleaks')", {"slug": "a", "scanner": "gitleaks"}),
            ("S(slug='k', scanner='t')", {"slug": "k", "scanner": "t"}),
            ("S('a')", {"slug": "a", "scanner": None}),
            ("S('a', NAME)", {"slug": "a", "scanner": None}),
            ("S(NAME, 'gitleaks')", None),
            ("other('a', 'b')", None),
            ("obj.plant(slug='a')", None),
        )
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(catalog_ast.ctor_identity(self.expr(source)), expected)

    def test_joined_path_and_spec_file_name(self):
        self.assertIsNone(extract_companion_path("MILL = ROOT\n"))
        self.assertIsNone(extract_companion_path('MILL = "a" / ROOT\n'))
        self.assertIsNone(extract_companion_path("MILL = ROOT.parent\n"))
        self.assertIsNone(extract_companion_path("OTHER = 'x'\n"))
        self.assertEqual(
            extract_companion_path('MILL = "experiments" / "x.py"\n'),
            "experiments/x.py",
        )
        loop = (
            "import importlib.util\n"
            'spec = importlib.util.spec_from_file_location("m")\n'
            'spec = importlib.util.spec_from_file_location("m", ROOT)\n'
            'spec = importlib.util.spec_from_file_location("m", ROOT / "ssr-mill-r9.py")\n'
        )
        extracted = extract_mill_catalog(loop, path="experiments/ssr-loop-r9.py")
        self.assertEqual(extracted["exec_target"], "ssr-mill-r9.py")
        self.assertEqual(extracted["kind"], cv.KIND_LOOP)


class SsrExtractRefusalTests(unittest.TestCase):
    def assert_unextractable(self, source: str):
        with self.assertRaisesRegex(ValueError, "has no extractable SSR catalog assignment"):
            extract_mill_catalog(source, path="experiments/ssr-mill-r9.py")

    def test_non_literal_dict_pairs_fall_through(self):
        self.assert_unextractable('PAIRS = [({"slug": NAME}, {"slug": "b"})]\n')

    def test_partially_constructed_pairs_fall_through(self):
        self.assert_unextractable(
            "PAIRS = [\n"
            '    (plant(slug="a", scanner="g"), plant(slug="b", scanner="t")),\n'
            '    (plant(scanner="x"), plant(slug="c")),\n'
            "]\n"
        )

    def test_bad_generated_rows_fall_through(self):
        for rows in (
            'ROWS = [("gitleaks", "a", 1)]',
            "ROWS = [NAME]",
            'ROWS = ["gitleaks"]',
            'ROWS = [("gitleaks",), ("t", "b")]',
            'ROWS = [(1, "a"), ("t", "b")]',
        ):
            with self.subTest(rows=rows):
                self.assert_unextractable(rows + "\n")

    def test_generated_rows_pair_successive_plants(self):
        extracted = extract_mill_catalog(
            'ROWS = [("gitleaks", "a", 1), ("trufflehog", "b", 2)]\n',
            path="experiments/ssr-mill-r9.py",
        )
        self.assertEqual(extracted["shape"], "rows-generated")
        self.assertEqual(extracted["catalog_first"], 9)
        self.assertEqual(extracted["first_slug"], "gitleaks-a")
        self.assertEqual(extracted["pairs"][0]["fail_slug"], "trufflehog-b")

    def test_later_non_literal_tails_and_scan_keep_the_last_literal(self):
        extracted = extract_mill_catalog(
            'SCAN = {"gitleaks": 1, "trufflehog": 2}\n'
            "SCAN = {NAME: 1}\n"
            'TAILS = ["a", "b"]\n'
            "TAILS = []\n"
            "TAILS = [1, 2]\n",
            path="experiments/ssr-mill-r9.py",
        )
        self.assertEqual(extracted["shape"], SHAPE_TAILS)
        self.assertEqual(extracted["scanners"], ["gitleaks", "trufflehog"])
        self.assertEqual(extracted["tails"], ["a", "b"])
        self.assertEqual(extracted["first_slug"], "gitleaks-a-leftover")

    def test_single_tail_is_unextractable(self):
        self.assert_unextractable('TAILS = ["a"]\n')

    def test_deferred_rows_refuse_a_pair_count_mismatch(self):
        record = {
            "kind": cv.KIND_PAIRS,
            "mill_id": "ssr-mill-r9",
            "path": "experiments/ssr-mill-r9.py",
            "shape": SHAPE_PLANT,
            "n_rows": 1,
            "pairs": [],
        }
        with self.assertRaisesRegex(ValueError, "ssr-mill-r9 deferred pairs 0 != n_rows 1"):
            deferred_pair_rows([record])
        with self.assertRaisesRegex(ValueError, "deferred pair rows 0 != pin 1"):
            deferred_pair_rows([], expected_rows=1)


class SsrInheritedScannerTests(unittest.TestCase):
    @staticmethod
    def tails_record(**overrides):
        record = {
            "shape": SHAPE_TAILS,
            "first_slug": None,
            "last_slug": None,
            "first_tail": "a",
            "last_success_tail": "c",
            "n_tails": 4,
            "tails": ["a", "b", "c", "d"],
            "scanners": [],
            "pairs": [],
        }
        record.update(overrides)
        return record

    def test_non_tails_record_is_returned_unchanged(self):
        record = {"shape": SHAPE_PLANT}
        self.assertIs(apply_inherited_scanners(record, ["gitleaks"]), record)

    def test_inherited_scanners_fill_slugs_and_pairs(self):
        filled = apply_inherited_scanners(self.tails_record(), ["gitleaks", "trufflehog"])
        self.assertEqual(filled["first_slug"], "gitleaks-a-leftover")
        self.assertEqual(filled["last_slug"], "gitleaks-c-leftover")
        self.assertEqual(len(filled["pairs"]), 2)

    def test_slug_fill_skips_incomplete_records(self):
        cases = (
            (self.tails_record(), []),
            (self.tails_record(first_tail=None, tails=None), ["gitleaks"]),
            (self.tails_record(n_tails=None, tails=None), ["gitleaks"]),
        )
        for record, scanners in cases:
            with self.subTest(record=record, scanners=scanners):
                self.assertIs(apply_inherited_scanners(record, scanners), record)

    def test_last_slug_needs_a_success_tail_and_two_tails(self):
        for overrides in ({"last_success_tail": None}, {"n_tails": 1}):
            with self.subTest(overrides=overrides):
                filled = apply_inherited_scanners(
                    self.tails_record(tails=["a"], **overrides), ["gitleaks"]
                )
                self.assertEqual(filled["first_slug"], "gitleaks-a-leftover")
                self.assertIsNone(filled["last_slug"])
                self.assertEqual(filled["pairs"], [])

    def test_local_scanners_win_and_existing_pairs_stay(self):
        local = apply_inherited_scanners(
            self.tails_record(first_slug="kept", scanners=["ggshield"]), ["gitleaks"]
        )
        self.assertEqual(local["first_slug"], "kept")
        self.assertEqual(local["pairs"][0]["success_scanner"], "ggshield")
        existing = self.tails_record(first_slug="kept", pairs=[{"success_slug": "p"}])
        self.assertIs(apply_inherited_scanners(existing, ["gitleaks"]), existing)


if __name__ == "__main__":
    unittest.main()
