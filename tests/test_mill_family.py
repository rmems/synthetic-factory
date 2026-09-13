#!/usr/bin/env python3
"""Foreign-mill detection on the shapes that defeated the earlier detectors.

The census of record EXP-G46-LEFTOVER-MILL-CENSUS-001 found 40 published
records that were dest-stamped (``meta.factory`` equal to the directory they
sit in), carried no ``leftover`` token in their id, and used a generic episode
slug with no destination-family field. Neither a factory-mix check nor a
dest-field-absence check can see those. These tests pin the id-prefix and
goal-family axes that do, and the accumulator and roll-up that report them.

The per-axis suites live in siblings named for the module each one exercises:
``test_mill_signals`` (what one record says about itself),
``test_mill_resolution`` (where each id prefix lives),
``test_mill_evidence`` (what a payload declares),
``test_mill_goal_family`` (what a goal vocabulary betrays), and
``test_mill_ownership`` (whether a run is owned well enough to export).
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
    GRAPHQL_NATIVE,
    SEARCH,
    SEARCH_NATIVE,
    STAMPEDE_CONTROLS,
    episode,
    index_of,
    stampede_index,
)
from mill_family import (  # noqa: E402
    REASON_FOREIGN_MILL_GOAL_FAMILY,
    REASON_FOREIGN_MILL_ID_PREFIX,
    REASON_FOREIGN_PAYLOAD_FACTORY,
    MillIndex,
    summarize,
)


class DestStampedMill(unittest.TestCase):
    """The 40-record class: dest-stamped, no leftover-in-id, generic slug."""

    def setUp(self):
        self.findings = {
            finding.record_id: finding for finding in stampede_index().findings()
        }

    def test_dest_stamped_foreign_mill_is_detected(self):
        for record in DEST_STAMPED_MILL:
            finding = self.findings.get(record["id"])
            self.assertIsNotNone(finding, record["id"])
            self.assertEqual(finding.factory, CACHE_STAMPEDE)
            self.assertEqual(finding.mill_prefix, "gql")
            self.assertIn(REASON_FOREIGN_MILL_ID_PREFIX, finding.reason_codes)
            self.assertEqual(finding.home_factories, (GRAPHQL,))

    def test_destination_controls_and_home_records_are_clean(self):
        for record in STAMPEDE_CONTROLS + GRAPHQL_NATIVE:
            self.assertNotIn(record["id"], self.findings, record["id"])

    def test_factory_mix_alone_cannot_see_them(self):
        """meta.factory is the destination, so the payload-factory axis is silent."""
        for record in DEST_STAMPED_MILL:
            self.assertEqual(record["meta"]["factory"], CACHE_STAMPEDE)
            finding = self.findings[record["id"]]
            self.assertNotIn(REASON_FOREIGN_PAYLOAD_FACTORY, finding.reason_codes)

    def test_leftover_in_id_is_not_the_mill_test(self):
        """No flagged id says 'leftover'; a destination id that does is clean."""
        for record in DEST_STAMPED_MILL:
            self.assertNotIn("leftover", record["id"])
        self.assertIn("leftover", STAMPEDE_CONTROLS[2]["id"])
        self.assertNotIn(STAMPEDE_CONTROLS[2]["id"], self.findings)

    def test_foreign_native_prefix_is_detected_even_with_leftover_in_id(self):
        stray = episode(
            "sir-r1400-leftover3c-vespa-handoff",
            "Repair Vespa index rebuild handoff after schema generation rollover",
            CACHE_STAMPEDE,
        )
        mills = index_of(
            (CACHE_STAMPEDE, STAMPEDE_CONTROLS + [stray]),
            (SEARCH, SEARCH_NATIVE),
        )
        finding = next(
            item for item in mills.findings() if item.record_id == stray["id"]
        )
        self.assertIn("leftover", stray["id"])
        self.assertIn(REASON_FOREIGN_MILL_ID_PREFIX, finding.reason_codes)
        self.assertEqual(finding.home_factories, (SEARCH,))

    def test_no_destination_family_field_is_required(self):
        """Generic episode slugs: nothing but goal/steps, so absence proves nothing."""
        for record in DEST_STAMPED_MILL + STAMPEDE_CONTROLS:
            self.assertEqual(
                sorted(record),
                ["goal", "id", "meta", "outcome", "reward", "steps"],
            )

    def test_summarize_reports_the_destination_table(self):
        report = summarize(stampede_index().findings())
        self.assertEqual(report["records"], len(DEST_STAMPED_MILL))
        self.assertEqual(
            report["by_factory"],
            {CACHE_STAMPEDE: {"records": 2, "foreign_prefixes": {"gql": 2}}},
        )
        # Both surviving axes agree on these two: a graphql-mill id prefix and
        # a graphql-mill goal vocabulary inside a cache-stampede directory.
        self.assertEqual(
            report["reason_codes"],
            {REASON_FOREIGN_MILL_ID_PREFIX: 2, REASON_FOREIGN_MILL_GOAL_FAMILY: 2},
        )
        self.assertEqual(
            report["record_ids"], sorted(record["id"] for record in DEST_STAMPED_MILL)
        )
        self.assertFalse(report["record_ids_truncated"])

    def test_summarize_truncates_long_id_lists(self):
        report = summarize(stampede_index().findings(), id_limit=1)
        self.assertEqual(len(report["record_ids"]), 1)
        self.assertTrue(report["record_ids_truncated"])


class MillIndexAccumulator(unittest.TestCase):
    """What the entry point accepts before any axis is resolved."""

    def test_empty_index_has_no_findings(self):
        self.assertEqual(MillIndex().findings(), ())
        self.assertEqual(summarize(())["records"], 0)

    def test_non_mapping_records_are_ignored(self):
        mills = MillIndex()
        mills.add(CACHE_STAMPEDE, ["not", "a", "record"], 0)
        mills.add(CACHE_STAMPEDE, None, 1)
        self.assertEqual(len(mills), 0)
        self.assertEqual(mills.findings(), ())


if __name__ == "__main__":
    unittest.main()
