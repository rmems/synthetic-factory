#!/usr/bin/env python3
"""The three mill signals one record carries about itself.

One record read in isolation: no corpus, no destination, no resolution. These
tests pin what ``mill_prefix``, ``record_id``, ``declared_factory``, and
``goal_family`` read out of a payload, including the shapes that carry no
signal at all -- an id with no round token, a non-mapping record, and the
shared leftover vocabulary every lane in this corpus writes.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

from mill_test_support import (  # noqa: E402
    CACHE_STAMPEDE,
    DEST_STAMPED_MILL,
)
from mill_family import (  # noqa: E402
    declared_factory,
    goal_family,
    mill_prefix,
    record_id,
)


class MillSignals(unittest.TestCase):
    def test_mill_prefix_parsing(self):
        self.assertEqual(mill_prefix({"id": "gql-r1405-postgraphile-wrap"}), "gql")
        self.assertEqual(mill_prefix({"id": "cst-r01-ttl-expiry"}), "cst")
        self.assertEqual(mill_prefix({"id": "dbc-r1410-bk-cachemount-l3"}), "dbc")
        # Published rounds include an underscored round token.
        self.assertEqual(mill_prefix({"id": "cst-r4_29-sentry-projects-list"}), "cst")
        # A round suffix letter is part of the round, not the mill.
        self.assertEqual(mill_prefix({"id": "rlb-r135b-retry-after"}), "rlb")

    def test_ids_without_a_round_token_have_no_mill_prefix(self):
        for identifier in ("smoke-e1", "episode-17", "gql", "GQL-R1-X", ""):
            self.assertIsNone(mill_prefix({"id": identifier}), identifier)
        self.assertIsNone(mill_prefix({}))
        self.assertIsNone(mill_prefix("not a record"))

    def test_record_id_falls_back_to_meta(self):
        self.assertEqual(record_id({"meta": {"id": "gql-r1-x"}}), "gql-r1-x")
        self.assertEqual(record_id({"id": " gql-r1-x "}), "gql-r1-x")
        self.assertIsNone(record_id({"id": ""}))

    def test_declared_factory_reads_meta(self):
        self.assertEqual(declared_factory(DEST_STAMPED_MILL[0]), CACHE_STAMPEDE)
        self.assertIsNone(declared_factory({"meta": {}}))
        self.assertIsNone(declared_factory({"meta": "cache"}))

    def test_goal_family_drops_shared_leftover_vocabulary(self):
        family = goal_family(DEST_STAMPED_MILL[0])
        self.assertIn("postgraphile", family)
        self.assertIn("wrapmass", family)
        # Every lane in this corpus writes leftover/fix goals, so those words
        # cannot identify a mill.
        for neutral in ("leftover", "fix", "drop", "plant", "lattice", "after"):
            self.assertNotIn(neutral, family)

    def test_goal_family_covers_both_preference_sides(self):
        pair = {
            "chosen": {"goal": "resolve singleflight stampede"},
            "rejected": {"goal": "resolve dataloader batching"},
        }
        self.assertEqual(
            goal_family(pair), frozenset({"resolve", "singleflight", "stampede", "dataloader", "batching"})
        )


if __name__ == "__main__":
    unittest.main()
