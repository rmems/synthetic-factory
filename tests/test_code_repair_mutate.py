#!/usr/bin/env python3
"""Single-span mutations: sites, exact inverse, verification, seeded choice."""

import ast
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from code_repair_test_support import fixture, mutate, oc, program, vocabulary as cv  # noqa: E402


class Sites(unittest.TestCase):
    def test_sites_are_the_boundary_comparisons_of_the_target_body(self):
        found = mutate.sites(program("rec_linear_search").text, "rec_linear_search")
        self.assertEqual(len(found), 5)
        self.assertEqual([s.original_text for s in found], ["<=", "<", "<=", "<", "<"])
        self.assertEqual([s.replacement_text for s in found], ["<", "<=", "<", "<=", "<="])
        self.assertEqual(found, tuple(sorted(found, key=lambda s: (s.start, s.end))))
        self.assertTrue(all(s.operator == cv.OPERATOR_COMPARISON_BOUNDARY for s in found))

    def test_a_function_without_boundary_comparisons_has_no_site(self):
        self.assertEqual(mutate.sites(program("is_square_free").text, "is_square_free"), ())
        self.assertEqual(mutate.sites("x = 1\n", "missing"), ())

    def test_every_fixture_site_rewrites_one_span_and_restores_exactly(self):
        for prog in fixture().programs:
            for site in mutate.sites(prog.text, prog.function):
                with self.subTest(program=prog.function, line=site.lineno):
                    mutated = mutate.apply(prog.text, site)
                    self.assertEqual(mutated[: site.start], prog.text[: site.start])
                    self.assertEqual(mutated[site.start + len(site.replacement_text):], prog.text[site.end:])
                    self.assertEqual(mutate.repair(mutated, site), prog.text)
                    self.assertIsNone(mutate.verify(prog.text, mutated, site, prog.function))

    def test_byte_offsets_survive_non_ascii_text_before_the_site(self):
        text = program("factorial").text.replace('"""\n    Calculate', '"""\n    Ünïcödé\n    Calculate', 1)
        (site,) = mutate.sites(text, "factorial")
        mutated = mutate.apply(text, site)
        self.assertIn("number <= 0", mutated)
        self.assertEqual(mutate.repair(mutated, site), text)
        self.assertIsNone(mutate.verify(text, mutated, site, "factorial"))


class Verification(unittest.TestCase):
    def setUp(self):
        self.prog = program("get_1s_count")
        (self.site,) = mutate.sites(self.prog.text, self.prog.function)

    def test_a_noop_rewrite_is_refused_before_execution(self):
        self.assertEqual(
            mutate.verify(self.prog.text, self.prog.text, self.site, self.prog.function),
            cv.SKIP_MUTATION_NOOP,
        )

    def test_a_rewrite_that_does_not_compile_is_refused(self):
        broken = self.prog.text.replace("number < 0", "number < ", 1)
        self.assertEqual(
            mutate.verify(self.prog.text, broken, self.site, self.prog.function),
            cv.SKIP_MUTATION_SYNTAX_ERROR,
        )

    def test_a_rewrite_that_is_not_the_declared_transform_is_unverifiable(self):
        other = self.prog.text.replace("number < 0", "number > 0", 1)
        self.assertEqual(
            mutate.verify(self.prog.text, other, self.site, self.prog.function),
            cv.SKIP_MUTATION_UNVERIFIABLE,
        )

    def test_a_rewrite_touching_the_docstring_is_refused(self):
        tampered = mutate.apply(self.prog.text, self.site).replace(">>> get_1s_count(0)\n    0", ">>> get_1s_count(0)\n    1", 1)
        self.assertEqual(
            mutate.verify(self.prog.text, tampered, self.site, self.prog.function),
            cv.SKIP_MUTATION_TOUCHES_DOCSTRING,
        )

    def test_the_mutant_differs_from_the_original_as_an_ast(self):
        mutated = mutate.apply(self.prog.text, self.site)
        original = ast.dump(ast.parse(self.prog.text))
        self.assertNotEqual(ast.dump(ast.parse(mutated)), original)
        self.assertIn(self.site.replacement_text, mutated)


class SeededChoice(unittest.TestCase):
    def test_the_same_seed_draws_the_same_sites(self):
        sites = mutate.sites(program("rec_linear_search").text, "rec_linear_search")
        first = [mutate.choose(oc.DrawStream(7), sites).start for _ in range(6)]
        second = [mutate.choose(oc.DrawStream(7), sites).start for _ in range(6)]
        self.assertEqual(first, second)
        stream = oc.DrawStream(7)
        drawn = {mutate.choose(stream, sites).start for _ in range(40)}
        self.assertGreater(len(drawn), 1)

    def test_site_json_carries_the_span_and_never_a_verdict(self):
        (site,) = mutate.sites(program("factorial").text, "factorial")
        payload = site.as_json()
        self.assertEqual(payload["original_text"], "<")
        self.assertEqual(payload["end_byte"] - payload["start_byte"], 1)
        self.assertFalse(set(payload) & oc.ORACLE_ONLY_KEYS)
        self.assertFalse(set(payload) & cv.ORACLE_LABEL_KEYS)


if __name__ == "__main__":
    unittest.main()
