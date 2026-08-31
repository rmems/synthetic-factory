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
    GRAPHQL,
    STAMPEDE_CONTROLS,
    index_of,
)
from mill_family import (  # noqa: E402
    REASON_FOREIGN_PAYLOAD_FACTORY,
    declared_factory,
    declared_factory_claims,
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

    def test_declared_factory_reads_consistent_preference_side_stamps(self):
        pair = {
            "chosen": {"meta": {"factory": CACHE_STAMPEDE}},
            "rejected": {"meta": {"factory": CACHE_STAMPEDE}},
        }
        self.assertEqual(declared_factory(pair), CACHE_STAMPEDE)
        pair["rejected"]["meta"]["factory"] = GRAPHQL
        self.assertIsNone(declared_factory(pair))

    def test_consistent_preference_sides_override_destination_wrapper_stamp(self):
        """Agreeing side stamps, not the destination wrapper, name the origin.

        #96 made ``declared_factory`` strict: a wrapper claim that contradicts
        its sides is no longer ownership evidence, so it can no longer define
        a prefix home. The override this test pins therefore resolves one
        layer out -- ``declared_factory_claims`` keeps both claims in
        wrapper-then-side order and the finding reports the side origin over
        the destination wrapper stamp.
        """

        pair = {
            "id": "cst-r08-dest-wrapped-side-origin",
            "goal": "fix verify",
            "meta": {"factory": CACHE_STAMPEDE, "round": 1},
            "chosen": {"goal": "fix verify", "meta": {"factory": GRAPHQL}},
            "rejected": {"goal": "fix verify", "meta": {"factory": GRAPHQL}},
        }
        # The wrapper never outvotes its sides: the clash names no owner...
        self.assertIsNone(declared_factory(pair))
        # ...both claims stay visible, so the origin is not dropped...
        self.assertEqual(declared_factory_claims(pair), (CACHE_STAMPEDE, GRAPHQL))

        # ...and the reported declaration is the side origin, not the
        # destination the wrapper stamps.
        findings = {
            finding.record_id: finding
            for finding in index_of(
                (CACHE_STAMPEDE, STAMPEDE_CONTROLS + [pair])
            ).findings()
        }
        self.assertIn(pair["id"], findings)
        finding = findings[pair["id"]]
        self.assertIn(REASON_FOREIGN_PAYLOAD_FACTORY, finding.reason_codes)
        self.assertEqual(finding.declared_factory, GRAPHQL)
        self.assertEqual(finding.expected_factory, CACHE_STAMPEDE)

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
