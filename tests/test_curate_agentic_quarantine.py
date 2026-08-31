#!/usr/bin/env python3
"""Quarantine of records whose mill is foreign to the directory they sit in."""

import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
PIPELINES = TESTS.parent / "pipelines"
for _path in (TESTS, PIPELINES):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import curate_agentic  # noqa: E402
from curate_agentic import (  # noqa: E402
    ACTION_EXCLUDED,
    REASON_FOREIGN_MILL_ID_PREFIX,
    REASON_FOREIGN_PAYLOAD_FACTORY,
    TRANSFORM_VERSION,
    curate_source,
)
from curate_agentic_fixtures import (  # noqa: E402
    DEST_STAMPED_MILL,
    GRAPHQL_NATIVE,
    STAMPEDE_CONTROLS,
    curate_mill_run,
    write_mill_run,
)


class ForeignMillQuarantine(unittest.TestCase):
    """Compose must quarantine records whose mill is foreign to the directory."""

    def test_dest_stamped_mill_is_excluded_from_the_cleaned_tree(self):
        run = curate_mill_run(list(STAMPEDE_CONTROLS) + [DEST_STAMPED_MILL])

        self.assertEqual(run["summary"]["input_records"], 5)
        self.assertEqual(run["summary"]["output_records"], 4)
        self.assertEqual(run["summary"]["transform"]["version"], "2")
        self.assertEqual(TRANSFORM_VERSION, "2")
        self.assertTrue(run["summary"]["mill_family"]["context_complete"])
        self.assertFalse(
            run["summary"]["mill_family"]["reference_scope_complete"]
        )
        self.assertTrue(run["summary"]["mill_family"]["quarantine_applied"])
        self.assertEqual(run["summary"]["quarantined_foreign_mill_records"], 1)
        emitted = {
            record["id"]
            for records in run["records_by_rel"].values()
            for record in records
        }
        self.assertNotIn(DEST_STAMPED_MILL["id"], emitted)
        for control in STAMPEDE_CONTROLS + GRAPHQL_NATIVE:
            self.assertIn(control["id"], emitted)

    def test_nested_batches_use_the_enclosing_factory_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "run"
            root.mkdir()
            write_mill_run(
                root, list(STAMPEDE_CONTROLS) + [DEST_STAMPED_MILL]
            )
            for factory in (
                "cache-stampede-factory",
                "graphql-nplusone-factory",
            ):
                directory = root / factory
                archive = directory / "archive"
                archive.mkdir()
                (directory / "batch-r01.jsonl").rename(
                    archive / "batch-r01.jsonl"
                )
            run = curate_source(root)

        self.assertEqual(
            run["summary"]["mill_family"]["context_factories"],
            ["cache-stampede-factory", "graphql-nplusone-factory"],
        )
        self.assertEqual(run["summary"]["quarantined_foreign_mill_records"], 1)
        self.assertNotIn(
            DEST_STAMPED_MILL["id"],
            {
                record["id"]
                for records in run["records_by_rel"].values()
                for record in records
            },
        )

    def test_suffixed_outer_snapshot_keeps_child_factory_roots(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "pre-window-factory"
            root.mkdir()
            write_mill_run(
                root, list(STAMPEDE_CONTROLS) + [DEST_STAMPED_MILL]
            )
            run = curate_source(root)

        self.assertEqual(
            run["summary"]["mill_family"]["context_factories"],
            ["cache-stampede-factory", "graphql-nplusone-factory"],
        )
        self.assertEqual(run["summary"]["quarantined_foreign_mill_records"], 1)

    def test_quarantine_decision_names_the_home_mill(self):
        run = curate_mill_run(list(STAMPEDE_CONTROLS) + [DEST_STAMPED_MILL])
        decision = next(
            item
            for item in run["decisions"]
            if item["source_path"].startswith("cache-stampede-factory")
            and item["action"] == ACTION_EXCLUDED
        )
        self.assertIn(REASON_FOREIGN_MILL_ID_PREFIX, decision["reason_codes"])
        # Dest-stamped: the payload-factory axis stays silent, so a factory-mix
        # check on its own would have let this through.
        self.assertNotIn(REASON_FOREIGN_PAYLOAD_FACTORY, decision["reason_codes"])
        self.assertIsNone(decision["output_id"])
        self.assertIsNone(decision["output_hash"])
        self.assertEqual(decision["mill_family"]["mill_prefix"], "gql")
        self.assertEqual(
            decision["mill_family"]["home_factories"], ["graphql-nplusone-factory"]
        )

    def test_summary_reports_the_quarantined_destination(self):
        run = curate_mill_run(list(STAMPEDE_CONTROLS) + [DEST_STAMPED_MILL])
        self.assertEqual(
            run["summary"]["mill_family"]["by_factory"],
            {
                "cache-stampede-factory": {
                    "records": 1,
                    "foreign_prefixes": {"gql": 1},
                }
            },
        )
        self.assertEqual(
            run["summary"]["reason_codes"].get(REASON_FOREIGN_MILL_ID_PREFIX), 1
        )

    def test_a_clean_run_quarantines_nothing(self):
        run = curate_mill_run(list(STAMPEDE_CONTROLS))
        self.assertEqual(run["summary"]["quarantined_foreign_mill_records"], 0)
        self.assertEqual(run["summary"]["output_records"], 4)
        self.assertEqual(run["summary"]["mill_family"]["records"], 0)
        self.assertNotIn(ACTION_EXCLUDED, run["summary"]["actions"])

    def test_quarantined_records_never_reach_a_written_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "run"
            root.mkdir()
            write_mill_run(root, list(STAMPEDE_CONTROLS) + [DEST_STAMPED_MILL])
            run = curate_source(root)
            out = Path(temporary) / "cleaned"
            curate_agentic.write_cleaned_tree(run, out)
            written = "\n".join(
                path.read_text(encoding="utf-8")
                for path in sorted(out.rglob("*.jsonl"))
            )
        self.assertNotIn(DEST_STAMPED_MILL["id"], written)
        for control in STAMPEDE_CONTROLS:
            self.assertIn(control["id"], written)


if __name__ == "__main__":
    unittest.main()
