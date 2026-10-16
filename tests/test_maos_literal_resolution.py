"""Pin ``maos.catalog``'s literal resolver through ``plants_from_source``.

Module constants and ``build_record`` locals are resolved without executing
the builder: supported arithmetic and containers bind, anything else (string
negation, division, dict spreads, calls) leaves the name unbound so the
``rec`` field that uses it is dropped.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from maos import catalog as cat
from maos._contract import MaosRefusal

_SOURCE = """
GEN_AT = '2026-09-02T00:00:00Z'
K = 3
ROUND = K * 4 - 2
NEG = -K
TITLE = 'LYO' + 'SHIELD'
EVENTS = [NEG, -1.5, (K,)]
BAD_NEG = -'s'
BAD_DIV = K / 2
BAD_SPREAD = {**{}}
BAD_CALL = make()

def build_record():
    state = {'domain': 'lyo', 'scenario_name': TITLE, 'nested': {'k': K}}
    rec = {
        'id': 'maos-r10-001',
        'title': TITLE,
        'meta': {'round': ROUND, 'run_label': BAD_DIV},
        'state': state,
        'safety_decision': {'decision': BAD_NEG, 'correctness': 'correct'},
        'spike_events': EVENTS,
        'raster': {'spikes': BAD_CALL},
        1: 'ignored',
    }
    return rec
"""


class LiteralResolutionTests(unittest.TestCase):
    def test_supported_literals_bind_and_unsupported_ones_drop_their_fields(self):
        (plant,) = cat.plants_from_source(_SOURCE, "fixture")
        self.assertEqual(plant.record_id, "maos-r10-001")
        self.assertEqual(plant.source_round, 10)
        self.assertEqual(plant.title, "LYOSHIELD")
        self.assertEqual((plant.domain, plant.scenario), ("lyo", "LYOSHIELD"))
        self.assertEqual(plant.run_label, "")
        self.assertEqual((plant.decision, plant.decision_correctness), ("", "correct"))
        self.assertEqual((plant.spike_events, plant.raster_spikes), (3, 0))
        self.assertEqual(plant.generated_at, "2026-09-02T00:00:00Z")
        self.assertEqual(plant.sim_or_real, "designed")

    def test_subtraction_and_negation_resolve_numbers(self):
        source = _SOURCE.replace("'round': ROUND", "'round': K - NEG - 1")
        (plant,) = cat.plants_from_source(source, "fixture")
        self.assertEqual(plant.source_round, 5)

    def test_identity_refusals_name_the_source(self):
        cases = (
            ("'id': 'maos-r10-001'", "'id': BAD_SPREAD", "fixture rec.id is missing"),
            ("'round': ROUND", "'round': NEG", "fixture meta.round is not a positive int"),
            ("'run_label': BAD_DIV", "'factory': 'other'", "fixture factory 'other'"),
            ("'run_label': BAD_DIV", "'generator': 'other'", "fixture generator 'other'"),
        )
        for old, new, message in cases:
            with self.subTest(message=message):
                with self.assertRaises(MaosRefusal) as caught:
                    cat.plants_from_source(_SOURCE.replace(old, new), "fixture")
                self.assertTrue(str(caught.exception).endswith(message), str(caught.exception))

    def test_a_builder_without_a_rec_dict_is_refused(self):
        for body in ("    rec = 5\n", "    other = {}\n"):
            with self.subTest(body=body), self.assertRaises(MaosRefusal) as caught:
                cat.plants_from_source("def build_record():\n" + body, "m.py")
            self.assertTrue(str(caught.exception).endswith("build_record has no rec dict"))


class NestingDepthTests(unittest.TestCase):
    """Long operator chains resolve as on main: one Python frame per nesting level."""

    def test_a_600_term_sum_and_a_600_deep_negation_resolve(self):
        for expr, expected in ((" + ".join(["1"] * 600), 600), ("-" * 600 + "7", 7)):
            with self.subTest(expected=expected):
                source = _SOURCE.replace("'round': ROUND", f"'round': {expr}")
                (plant,) = cat.plants_from_source(source, "m.py")
                self.assertEqual(plant.source_round, expected)

    def test_a_601_term_string_sum_reaches_the_round_check(self):
        chain = " + ".join(['"a"'] * 601)
        source = f"def build_record():\n    rec = {{'id': 'x', 'n': {chain}}}\n"
        with self.assertRaises(MaosRefusal) as caught:
            cat.plants_from_source(source, source_name="m.py")
        self.assertTrue(str(caught.exception).endswith("m.py meta.round is not a positive int"))


if __name__ == "__main__":
    unittest.main()
