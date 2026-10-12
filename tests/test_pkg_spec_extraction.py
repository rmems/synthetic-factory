"""Pin ``pkg.catalog``'s AST spec extraction and plant-field refusals.

Synthetic mill sources drive the ``add()``/``append`` scan, the dict and
``_ok``/``_fail`` call spec readers, and each per-field refusal message
through the public ``plants_from_source`` / ``plant_from_mapping`` surface.
"""

from __future__ import annotations

import dataclasses
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from pkg import catalog as cat
from pkg._contract import PkgRefusal

_OK = "{'slug': 'ok-slug', 'plant': 'p1', 'seed': 's', 'first': 'f', 'change': 'c', 'term': 't'}"
_FAIL = "{'slug': 'fail-slug', 'plant': 'p2', 'seed': 's', 'first': 'f', 'change': 'c', 'term': 't'}"

_DYNAMIC = f"""
CATALOG_FIRST = 7

def _pairs():
    out = []
    def add(ok, fail):
        marker = 1
        print('noise')
        out.append()
        out.append(ok)
        out.append(('cosign_reusable', ok))
        out.append(('cosign_reusable', ok, 'fail_leftover', fail))
    add({_OK}, {_FAIL})
"""


class DynamicPairsTests(unittest.TestCase):
    def test_add_helper_kinds_come_from_the_first_four_tuple_append(self):
        plants = cat.plants_from_source(_DYNAMIC, "dyn")
        self.assertEqual([(p.record_id, p.role, p.kind) for p in plants], [
            ("pkg-r7-ok-slug", "ok", "cosign_reusable"),
            ("pkg-r7-fail-slug", "fail", "fail_leftover"),
        ])

    def test_add_helper_without_a_four_tuple_append_is_refused(self):
        source = "CATALOG_FIRST = 7\ndef _pairs():\n    def add(a, b):\n        out.append((1, 2))\n    add(1, 2)\n"
        with self.assertRaisesRegex(PkgRefusal, "add\\(\\) does not append a 4-tuple"):
            cat.plants_from_source(source)


class SpecReaderTests(unittest.TestCase):
    @staticmethod
    def _plants(ok_spec: str, fail_spec: str) -> tuple:
        source = (
            "CATALOG_FIRST = 9\n"
            f"def _pairs():\n    return [('cosign_reusable', {ok_spec}, 'fail_leftover', {fail_spec})]\n"
        )
        return cat.plants_from_source(source)

    def test_dict_specs_skip_non_string_keys_spreads_and_non_string_values(self):
        ok_spec = _OK[:-1] + ", 1: 'x', **extra, 'goal': 5, 'plan': 'kept'}"
        ok, _fail = self._plants(ok_spec, _FAIL)
        self.assertEqual((ok.slug, ok.goal, ok.plan), ("ok-slug", "", "kept"))

    def test_call_specs_skip_spread_keywords_and_refuse_unknown_builders(self):
        ok_spec = "_ok(slug='ok-slug', plant='p1', seed='s', first='f', change='c', term='t', goal=1, **extra)"
        ok, _fail = self._plants(ok_spec, _FAIL)
        self.assertEqual((ok.slug, ok.goal), ("ok-slug", ""))
        with self.assertRaisesRegex(PkgRefusal, "spec call must be one of .*, got _bad"):
            self._plants("_bad(slug='x')", _FAIL)

    def test_specs_that_are_neither_dicts_nor_named_calls_are_refused(self):
        for spec in ("[1]", "obj.make(slug='x')"):
            with self.subTest(spec=spec), self.assertRaisesRegex(PkgRefusal, "spec must be a dict"):
                self._plants(spec, _FAIL)


class PlantFieldTests(unittest.TestCase):
    def setUp(self):
        self.base = dataclasses.asdict(cat.load_catalog().plants[0])

    def _refusal(self, **overrides) -> str:
        with self.assertRaises(PkgRefusal) as caught:
            cat.plant_from_mapping(dict(self.base, **overrides), "w")
        return str(caught.exception)

    def test_each_field_rule_names_the_field(self):
        cases = (
            ({"source_round": 0}, "w.source_round must be a positive int, got 0"),
            ({"source_round": True}, "w.source_round must be a positive int, got True"),
            ({"index": 3}, "w.index must be 1 or 2, got 3"),
            ({"slug": 5}, "w.slug must be a string, got 5"),
            ({"goal": 5}, "w.goal must be a string, got 5"),
            ({"slug": ""}, "w.slug must be a non-empty string, got ''"),
            ({"role": "maybe"}, "w.role must be ok or fail, got 'maybe'"),
            ({"kind": "fail_leftover"}, "w.kind 'fail_leftover' is not an ok builder"),
            ({"role": "fail"}, "w.kind must be fail_leftover, got 'cosign_reusable'"),
            ({"record_id": "pkg-r1-x"}, "w.record_id must be pkg-r163-"),
            ({"index": 0, "slug": ""}, "w.index must be 1 or 2, got 0"),
        )
        for overrides, message in cases:
            with self.subTest(overrides=overrides):
                self.assertIn(message, self._refusal(**overrides))

    def test_empty_leftover_goal_and_plan_are_allowed(self):
        plant = cat.plant_from_mapping(dict(self.base, leftover="", goal="", plan=""), "w")
        self.assertEqual((plant.leftover, plant.goal, plant.plan), ("", "", ""))


class PairListTests(unittest.TestCase):
    def test_a_module_level_pairs_list_is_read_when_there_is_no_pairs_function(self):
        source = (
            "CATALOG_FIRST = 7\nOTHER = 1\nA = B = 2\nPAIRS = 5\n"
            f"PAIRS = [('cosign_reusable', {_OK}, 'fail_leftover', {_FAIL})]\n"
        )
        plants = cat.plants_from_source(source, "module")
        self.assertEqual([(p.record_id, p.role) for p in plants], [
            ("pkg-r7-ok-slug", "ok"),
            ("pkg-r7-fail-slug", "fail"),
        ])

    def test_missing_or_malformed_pair_lists_are_refused(self):
        cases = (
            ("CATALOG_FIRST = 7\ndef _pairs():\n    pass\n", "_pairs() has no nested add() helper"),
            ("CATALOG_FIRST = 7\nX = 1\n", "source has no _pairs() list"),
            ("CATALOG_FIRST = 7\nPAIRS = [(1, 2)]\n", "each catalog row must be a 4-tuple"),
        )
        for source, message in cases:
            with self.subTest(message=message), self.assertRaises(PkgRefusal) as caught:
                cat.plants_from_source(source, "module")
            self.assertIn(message, str(caught.exception))


if __name__ == "__main__":
    unittest.main()
