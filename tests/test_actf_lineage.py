#!/usr/bin/env python3
"""ACTF lineage reader enumerates the recover-grok tree and fails closed."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from actf_test_support import FIXTURE_TREE, cv, dumps_exact_json, lineage


class LineageTests(unittest.TestCase):
    def test_the_fixture_tree_has_two_actf_lineages_and_skips_ttf(self):
        trees = lineage.read_recovery_tree(FIXTURE_TREE)
        self.assertEqual([item.path_key for item in trees], [
            "actf-r02--d7a6007e9fe7",
            "actf-r10--fd6829e8acef",
        ])
        listed = lineage.by_original_path(FIXTURE_TREE)
        self.assertTrue((listed / "ttf-r01--deadbeef0001").is_dir())

    def test_the_exact_lineage_keeps_one_version_and_no_fragments(self):
        exact = {item.path_key: item for item in lineage.read_recovery_tree(FIXTURE_TREE)}[
            "actf-r10--fd6829e8acef"
        ]
        self.assertTrue(exact.is_recoverable)
        self.assertEqual(exact.classification, cv.CLASSIFICATION_EXACT)
        self.assertEqual(exact.version_count, 1)
        self.assertEqual(exact.versions[0].version_label, "v0001")
        self.assertEqual(exact.versions[0].basename, "gen.py")
        self.assertEqual(exact.versions[0].version_id, "actf-r10--fd6829e8acef:v0001")
        self.assertEqual(exact.fragments, ())

    def test_the_unrecoverable_lineage_has_no_versions_but_keeps_fragments(self):
        unrecoverable = {
            item.path_key: item for item in lineage.read_recovery_tree(FIXTURE_TREE)
        }["actf-r02--d7a6007e9fe7"]
        self.assertFalse(unrecoverable.is_recoverable)
        self.assertEqual(unrecoverable.versions, ())
        self.assertEqual(len(unrecoverable.fragments), 1)
        self.assertIsNotNone(unrecoverable.fragments[0].new_path)
        self.assertTrue(unrecoverable.fragments[0].new_path.is_file())

    def test_by_original_path_accepts_the_nested_directory(self):
        nested = FIXTURE_TREE / "recovered_sources" / "by-original-path"
        self.assertEqual(lineage.by_original_path(nested), nested)
        self.assertEqual(
            [item.path_key for item in lineage.read_recovery_tree(nested)],
            [item.path_key for item in lineage.read_recovery_tree(FIXTURE_TREE)],
        )

    def test_a_missing_recovery_root_is_refused(self):
        with TemporaryDirectory() as tmp:
            with self.assertRaises(cv.ActfRefusal) as caught:
                lineage.read_recovery_tree(Path(tmp) / "missing")
            self.assertEqual(caught.exception.code, cv.FINDING_RECOVERY_ROOT_MISSING)

    def test_a_path_key_mismatch_is_refused(self):
        with TemporaryDirectory() as tmp:
            root = _write_lineage(
                Path(tmp),
                dir_name="actf-r99--mismatch",
                path_key="actf-r99--other",
                classification="exact",
                version_count=0,
            )
            with self.assertRaises(cv.ActfRefusal) as caught:
                lineage.read_recovery_tree(root)
            self.assertEqual(caught.exception.code, cv.FINDING_PATH_KEY_MISMATCH)

    def test_an_unknown_classification_is_refused(self):
        with TemporaryDirectory() as tmp:
            root = _write_lineage(
                Path(tmp),
                dir_name="actf-r99--class",
                path_key="actf-r99--class",
                classification="guessed",
                version_count=0,
            )
            with self.assertRaises(cv.ActfRefusal) as caught:
                lineage.read_recovery_tree(root)
            self.assertEqual(caught.exception.code, cv.FINDING_UNKNOWN_CLASSIFICATION)

    def test_a_version_count_mismatch_is_refused(self):
        with TemporaryDirectory() as tmp:
            root = _write_lineage(
                Path(tmp),
                dir_name="actf-r99--count",
                path_key="actf-r99--count",
                classification="exact",
                version_count=2,
            )
            with self.assertRaises(cv.ActfRefusal) as caught:
                lineage.read_recovery_tree(root)
            self.assertEqual(caught.exception.code, cv.FINDING_VERSION_COUNT_MISMATCH)

    def test_duplicate_keys_in_path_json_are_refused(self):
        with TemporaryDirectory() as tmp:
            listed = Path(tmp) / "recovered_sources" / "by-original-path" / "actf-r99--dup"
            listed.mkdir(parents=True)
            (listed / "path.json").write_text(
                '{"path_key":"actf-r99--dup","path_key":"other"}\n',
                encoding="utf-8",
            )
            with self.assertRaises(cv.ActfRefusal) as caught:
                lineage.read_recovery_tree(Path(tmp))
            self.assertEqual(caught.exception.code, cv.FINDING_PATH_JSON_INVALID)

    def test_path_json_round_trips_through_exact_json(self):
        path = (
            FIXTURE_TREE / "recovered_sources" / "by-original-path"
            / "actf-r10--fd6829e8acef" / "path.json"
        )
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertIn("path_key", dumps_exact_json(payload))


def _write_lineage(
    tmp: Path,
    *,
    dir_name: str,
    path_key: str,
    classification: str,
    version_count: int,
) -> Path:
    listed = tmp / "recovered_sources" / "by-original-path" / dir_name
    listed.mkdir(parents=True)
    payload = {
        "path_key": path_key,
        "original_path": "/tmp/actf/gen.py",
        "original_basename": "gen.py",
        "classification": classification,
        "version_count": version_count,
    }
    (listed / "path.json").write_text(json.dumps(payload) + "\n", encoding="utf-8")
    return tmp


if __name__ == "__main__":
    unittest.main()
