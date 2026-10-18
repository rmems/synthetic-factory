#!/usr/bin/env python3
"""Cleaned-destination tests for the curation gate (pipelines/curate_gate.py).

The cleaned destination the curation gate writes: a brand-new, confined path
(a symlink is refused without echoing its spelling), disjoint from the source
run and outside outputs/raw/, published atomically from a re-authenticated
staging tree, with nothing left behind on failure.
"""

import sys
import unittest
from pathlib import Path
from unittest import mock

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from curate_gate_test_support import CurateGateAssertionsMixin, temp_root  # noqa: E402
from gate_fixture import PIPELINES, GateFixture  # noqa: E402

if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import curate_gate  # noqa: E402


class CleanedDestinationTests(CurateGateAssertionsMixin, unittest.TestCase):
    """Integration writes only to a new destination and fails closed."""

    def setUp(self):
        self.root = temp_root(self)

    def test_confined_path_redacts_a_leaf_symlink_spelling(self):
        target = self.root / "target.json"
        target.touch()
        marker_name = "operator-redaction-marker-symlink"
        link = self.root / marker_name
        link.symlink_to(target)

        with self.assertRaises(curate_gate.GateError) as raised:
            curate_gate._confined_path(str(link))

        self.assertEqual(str(raised.exception), "the path is a symlink")
        self.assertNotIn(marker_name, str(raised.exception))

    def test_integrate_refuses_an_existing_cleaned_destination(self):
        fixture = GateFixture(self.root)
        fixture.cleaned.mkdir(parents=True)
        self.assertEqual(fixture.integrate(), 2)

    def test_integrate_refuses_a_dangling_destination_symlink(self):
        fixture = GateFixture(self.root)
        target = self.root / "must-not-be-created"
        self.symlink_or_skip(fixture.cleaned, target, directory=True)

        self.assert_integrate_refused(fixture, "existing cleaned destination")
        self.assertFalse(target.exists())

    def test_destinations_beneath_raw_output_are_rejected(self):
        fixture = GateFixture(self.root)
        raw_root = self.root / "outputs" / "raw"
        raw_root.mkdir(parents=True)
        fixture.cleaned = raw_root / "cleaned-attempt"

        with mock.patch.object(curate_gate, "RAW_OUTPUT_ROOT", raw_root.resolve()):
            self.assertEqual(fixture.integrate(), 2)
        self.assertFalse(fixture.cleaned.exists())

    def test_cleaned_destination_must_be_disjoint_from_source_run(self):
        for name, destination in (
            ("equal", lambda fixture: fixture.source_run),
            ("inside", lambda fixture: fixture.source_run / "cleaned"),
            ("containing", lambda fixture: fixture.root),
        ):
            with self.subTest(name=name):
                fixture = GateFixture(self.root / name)
                self.assert_integrate_refused(
                    fixture,
                    "must be disjoint after symlink resolution",
                    destination=destination(fixture),
                )

    def test_cleaned_destination_symlink_alias_of_source_run_is_rejected(self):
        fixture = GateFixture(self.root)
        alias = self.root / "raw-alias"
        self.symlink_or_skip(alias, fixture.source_run, directory=True)

        self.assert_integrate_refused(
            fixture,
            "must be disjoint after symlink resolution",
            destination=alias / "cleaned",
        )
        self.assertFalse((fixture.source_run / "cleaned").exists())

    def test_a_failed_plan_leaves_no_partial_destination(self):
        fixture = GateFixture(self.root)
        for path in (fixture.lane_tag / "thalamic-mini").glob("*.jsonl"):
            path.unlink()
        self.assertEqual(fixture.integrate(), 2)
        self.assertFalse(fixture.cleaned.exists())

    def test_integration_failure_removes_the_staged_destination(self):
        fixture = GateFixture(self.root)
        with mock.patch.object(
            curate_gate, "run_gates", side_effect=curate_gate.GateError("gate exploded")
        ):
            self.assertEqual(fixture.integrate(), 2)

        self.assertFalse(fixture.cleaned.exists())
        self.assertEqual(list(self.root.glob(".cleaned-v1.staging-*")), [])

    def _assert_publish_refused(self, fixture, before_publish, message):
        """Run a refused `integrate` with ``before_publish`` ahead of the no-replace rename."""
        original = curate_gate._rename_noreplace

        def hooked_publish(source, destination, label, expected_tree):
            before_publish(source, destination)
            return original(source, destination, label, expected_tree)

        with mock.patch.object(
            curate_gate,
            "_rename_noreplace",
            side_effect=hooked_publish,
        ):
            self.assert_integrate_refused(fixture, message)

    def test_integration_atomically_refuses_a_concurrent_destination(self):
        fixture = GateFixture(self.root)
        reserved_inodes = []

        def reserve_destination(_source, destination):
            destination.mkdir(parents=True)
            reserved_inodes.append(destination.stat().st_ino)

        self._assert_publish_refused(
            fixture,
            reserve_destination,
            "refusing to overwrite an existing cleaned destination",
        )
        self.assertEqual(fixture.cleaned.stat().st_ino, reserved_inodes[0])
        self.assertEqual(list(fixture.cleaned.iterdir()), [])
        self.assertEqual(list(self.root.glob(".cleaned-v1.staging-*")), [])

    def test_integration_publisher_reauthenticates_the_staging_tree(self):
        fixture = GateFixture(self.root)

        def corrupt_staged_corpus(source, _destination):
            corpus = source / "thalamic-mini" / "batch-r02.jsonl"
            corpus.write_text("{invalid-json\n", encoding="utf-8")

        self._assert_publish_refused(
            fixture,
            corrupt_staged_corpus,
            "staging tree changed after final validation",
        )
        self.assertFalse(fixture.cleaned.exists())
        self.assertEqual(list(self.root.glob(".cleaned-v1.staging-*")), [])

    def _assert_staging_snapshot_rejects(self, make_link, unavailable, expected):
        """Stage one linked file and assert the staging-tree snapshot refuses it."""
        staged = self.root / "staged"
        staged.mkdir()
        target = self.root / "target.jsonl"
        target.write_text("{}\n", encoding="utf-8")
        try:
            make_link(staged / "alias.jsonl", target)
        except (OSError, NotImplementedError):
            self.skipTest(unavailable)

        with self.assertRaisesRegex(curate_gate.GateError, expected):
            curate_gate._tree_snapshot(staged)

    def test_staging_tree_snapshot_rejects_a_symlink(self):
        self._assert_staging_snapshot_rejects(
            Path.symlink_to,
            "symlinks are unavailable on this platform",
            "contains a symlink",
        )

    def test_staging_tree_snapshot_rejects_a_hardlink(self):
        self._assert_staging_snapshot_rejects(
            Path.hardlink_to,
            "hard links are unavailable on this platform",
            "multiply linked",
        )

if __name__ == '__main__':
    unittest.main()
