#!/usr/bin/env python3
"""Single-span mutations: sites, exact inverse, verification, seeded choice."""

import ast
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from code_repair_test_support import (  # noqa: E402
    boundary_site, fixture, mutate, oc, program, vocabulary as cv,
)


def boundary_sites(text, function):
    return tuple(s for s in mutate.sites(text, function) if s.operator == cv.OPERATOR_COMPARISON_BOUNDARY)


class DefinitionTimeNodes(unittest.TestCase):
    def test_defaults_annotations_and_decorators_are_never_sites(self):
        """Codex on #197: only the body is the behaviour the doctests specify."""

        text = (
            "def f(x: int = (1 < 2), y=[i for i in range(3) if i < 2]) -> bool:\n"
            "    '''\n    >>> f(0)\n    True\n    >>> f(1)\n    True\n    '''\n"
            "    return x <= 2\n"
        )
        found = mutate.sites(text, "f")
        self.assertIn("<=", [s.original_text for s in found])
        self.assertTrue(all(s.lineno > 1 for s in found), [s.original_text for s in found])


class Sites(unittest.TestCase):
    def test_sites_are_the_boundary_comparisons_of_the_target_body(self):
        found = boundary_sites(program("rec_linear_search").text, "rec_linear_search")
        self.assertEqual(len(found), 5)
        self.assertEqual([s.original_text for s in found], ["<=", "<", "<=", "<", "<"])
        self.assertEqual([s.replacement_text for s in found], ["<", "<=", "<", "<=", "<="])
        self.assertEqual(found, tuple(sorted(found, key=lambda s: (s.start, s.end))))
        self.assertTrue(all(s.operator == cv.OPERATOR_COMPARISON_BOUNDARY for s in found))

    def test_a_function_without_boundary_comparisons_has_no_site(self):
        self.assertEqual(boundary_sites(program("is_square_free").text, "is_square_free"), ())
        self.assertEqual(mutate.sites("x = 1\n", "missing"), ())

    def test_every_fixture_site_rewrites_one_span_and_restores_exactly(self):
        for prog in fixture().programs:
            for site in boundary_sites(prog.text, prog.function):
                with self.subTest(program=prog.function, line=site.lineno):
                    mutated = mutate.apply(prog.text, site)
                    self.assertEqual(mutated[: site.start], prog.text[: site.start])
                    self.assertEqual(mutated[site.start + len(site.replacement_text):], prog.text[site.end:])
                    self.assertEqual(mutate.repair(mutated, site), prog.text)
                    self.assertIsNone(mutate.verify(prog.text, mutated, site, prog.function))

    def test_byte_offsets_survive_non_ascii_text_before_the_site(self):
        text = program("factorial").text.replace('"""\n    Calculate', '"""\n    Ünïcödé\n    Calculate', 1)
        (site,) = boundary_sites(text, "factorial")
        mutated = mutate.apply(text, site)
        self.assertIn("number <= 0", mutated)
        self.assertEqual(mutate.repair(mutated, site), text)
        self.assertIsNone(mutate.verify(text, mutated, site, "factorial"))


class Verification(unittest.TestCase):
    def setUp(self):
        self.prog = program("get_1s_count")
        self.site = boundary_site(self.prog)

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
        sites = boundary_sites(program("rec_linear_search").text, "rec_linear_search")
        first = [mutate.choose(oc.DrawStream(7), sites).start for _ in range(6)]
        second = [mutate.choose(oc.DrawStream(7), sites).start for _ in range(6)]
        self.assertEqual(first, second)
        stream = oc.DrawStream(7)
        drawn = {mutate.choose(stream, sites).start for _ in range(40)}
        self.assertGreater(len(drawn), 1)

    def test_site_json_carries_the_span_and_never_a_verdict(self):
        (site,) = boundary_sites(program("factorial").text, "factorial")
        payload = site.as_json()
        self.assertEqual(payload["original_text"], "<")
        self.assertEqual(payload["end_byte"] - payload["start_byte"], 1)
        self.assertFalse(set(payload) & oc.ORACLE_ONLY_KEYS)
        self.assertFalse(set(payload) & cv.ORACLE_LABEL_KEYS)


if __name__ == "__main__":
    unittest.main()


class FiveOperators(unittest.TestCase):
    """Every operator class on the fixture programs: real sites, exact inverse, verified transform."""

    def sites_of(self, function, operator):
        prog = program(function)
        found = mutate.sites(prog.text, prog.function, prog.want_kind)
        return prog, [s for s in found if s.operator == operator]

    def test_every_operator_class_yields_sound_sites_somewhere_in_the_fixture(self):
        seen = set()
        for prog in fixture().programs:
            for site in mutate.sites(prog.text, prog.function, prog.want_kind):
                seen.add(site.operator)
                mutated = mutate.apply(prog.text, site)
                with self.subTest(program=prog.function, operator=site.operator, variant=site.variant):
                    self.assertIsNone(mutate.verify(prog.text, mutated, site, prog.function))
                    self.assertEqual(mutate.repair(mutated, site), prog.text)
                    self.assertNotEqual(mutated, prog.text)
        self.assertEqual(seen, set(cv.OPERATORS))

    def test_arithmetic_swaps_binary_and_augmented_operators(self):
        _prog, found = self.sites_of("sum_of_digits", cv.OPERATOR_ARITHMETIC)
        texts = {(s.original_text, s.replacement_text) for s in found}
        self.assertEqual(texts, {("+=", "-="), ("%", "//"), ("//=", "%=")})

    def test_boolean_condition_covers_equality_keyword_swap_and_dropped_not(self):
        prog, found = self.sites_of("rec_linear_search", cv.OPERATOR_BOOLEAN_CONDITION)
        variants = {(s.variant, s.original_text, s.replacement_text) for s in found}
        self.assertIn(("drop_not", "not ", ""), variants)
        self.assertIn(("swap", "and", "or"), variants)
        self.assertIn(("equality", "==", "!="), variants)
        dropped = next(s for s in found if s.variant == "drop_not")
        self.assertIn("if (0 <= high", mutate.apply(prog.text, dropped))

    def test_return_value_offsets_numeric_results_and_negates_boolean_ones(self):
        prog, found = self.sites_of("rec_linear_search", cv.OPERATOR_RETURN_VALUE)
        self.assertEqual(prog.want_kind, "numeric")
        replacements = {s.replacement_text for s in found}
        self.assertTrue({"0", "-2", "low + 1", "low - 1", "high + 1"}.issubset(replacements), replacements)
        prog, found = self.sites_of("is_square_free", cv.OPERATOR_RETURN_VALUE)
        self.assertEqual(prog.want_kind, "bool")
        (negated,) = found
        # A comparison binds tighter than ``not``, so no parentheses are needed.
        self.assertEqual(negated.replacement_text, "not len(set(factors)) == len(factors)")

    def test_off_by_one_moves_boundary_literals_and_never_below_zero(self):
        _prog, found = self.sites_of("factorial", cv.OPERATOR_OFF_BY_ONE)
        moves = sorted((s.lineno, s.original_text, s.replacement_text) for s in found)
        self.assertEqual([m[1:] for m in moves], [("0", "1"), ("1", "0"), ("1", "0"), ("1", "2"), ("1", "2")])
        _prog, found = self.sites_of("rec_linear_search", cv.OPERATOR_OFF_BY_ONE)
        self.assertEqual({s.replacement_text for s in found}, {"1"})

    def test_want_kind_is_derived_from_the_docstring_wants(self):
        self.assertEqual(program("get_1s_count").want_kind, "numeric")
        self.assertEqual(program("is_square_free").want_kind, "bool")
        self.assertIsNone(program("factorial").want_kind)
        self.assertIsNone(program("abs_val").want_kind)

    def test_a_site_locates_its_node_exactly_for_the_transform(self):
        _prog, found = self.sites_of("get_1s_count", cv.OPERATOR_ARITHMETIC)
        for site in found:
            payload = site.as_json()
            self.assertEqual({"node", "start_byte", "end_byte", "lineno", "col_offset", "original_text",
                              "replacement_text", "node_lineno", "node_col_offset", "node_end_lineno",
                              "node_end_col_offset", "op_index"}, set(payload))
