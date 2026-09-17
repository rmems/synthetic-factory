#!/usr/bin/env python3
"""ACTF records assemble exclusions and refuse raw-tree / vendor roots."""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from actf_test_support import FIXTURE_TREE, cli, cv, lineage, records


class RecordsTests(unittest.TestCase):
    def test_the_fixture_tree_yields_one_kept_record_and_one_exclusion(self):
        extracted = records.scan_recovery_tree(FIXTURE_TREE)
        self.assertEqual(len(extracted), 2)
        kept = [item for item in extracted if not item.excluded]
        excluded = [item for item in extracted if item.excluded]
        self.assertEqual(len(kept), 1)
        self.assertEqual(len(excluded), 1)
        self.assertEqual(kept[0].path_key, "actf-r10--fd6829e8acef")
        self.assertEqual(kept[0].version_label, "v0001")
        self.assertEqual(kept[0].syntax_status, cv.SYNTAX_OK)
        self.assertEqual(kept[0].features["episode_functions"], ["ep1"])
        self.assertEqual(kept[0].features["factory_literals"], [cv.FACTORY])
        self.assertIn(cv.FINDING_FILE_WRITE, [item["category"] for item in kept[0].operations])
        self.assertIn(cv.FINDING_PROCESS_EXECUTION, [item["category"] for item in kept[0].operations])
        self.assertEqual(excluded[0].reason, cv.REASON_UNRECOVERABLE_LINEAGE)
        self.assertEqual(len(kept[0].source_sha256), 64)

    def test_summarize_counts_lineages_and_findings(self):
        summary = records.summarize(records.scan_recovery_tree(FIXTURE_TREE))
        self.assertEqual(summary["family"], cv.FAMILY)
        self.assertEqual(summary["corpus"], cv.CORPUS)
        self.assertEqual(summary["lineages"], 2)
        self.assertEqual(summary["records"], 2)
        self.assertEqual(summary["excluded"], 1)
        self.assertEqual(summary["by_classification"], {
            cv.CLASSIFICATION_EXACT: 1,
            cv.CLASSIFICATION_UNRECOVERABLE: 1,
        })
        self.assertEqual(summary["by_syntax_status"], {cv.SYNTAX_OK: 1})
        self.assertEqual(summary["exclusions"], {cv.REASON_UNRECOVERABLE_LINEAGE: 1})
        self.assertGreaterEqual(summary["by_operation_category"][cv.FINDING_FILE_WRITE], 1)

    def test_a_syntax_error_version_is_excluded_via_a_temp_tree(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            listed = root / "recovered_sources" / "by-original-path" / "actf-r77--syntax"
            version_dir = listed / "versions" / "v0001"
            version_dir.mkdir(parents=True)
            (listed / "path.json").write_text(
                json.dumps({
                    "path_key": "actf-r77--syntax",
                    "original_path": "/tmp/actf-r77/gen.py",
                    "original_basename": "gen.py",
                    "classification": "exact",
                    "version_count": 1,
                }) + "\n",
                encoding="utf-8",
            )
            (version_dir / "gen.py").write_text("def broken(\n", encoding="utf-8")
            extracted = records.scan_recovery_tree(root)
            self.assertEqual(len(extracted), 1)
            self.assertTrue(extracted[0].excluded)
            self.assertEqual(extracted[0].reason, cv.REASON_SYNTAX_ERROR)
            self.assertEqual(extracted[0].syntax_status, cv.SYNTAX_ERROR)

    def test_recovery_root_under_outputs_raw_is_refused(self):
        with self.assertRaises(cv.ActfRefusal) as caught:
            records.scan_recovery_tree(Path("/tmp/outputs/raw/actf"))
        self.assertEqual(caught.exception.code, cv.FINDING_RECOVERY_ROOT_UNDER_RAW)

    def test_a_vendored_mill_destination_is_refused(self):
        with self.assertRaises(cv.ActfRefusal) as caught:
            records.scan_recovery_tree(Path("/tmp/actf-mill-r10.py"))
        self.assertEqual(caught.exception.code, cv.FINDING_VENDOR_PATH)

    def test_cli_scan_prints_the_fixture_summary(self):
        buf = StringIO()
        with patch("sys.stdout", buf):
            code = cli.run(["scan", str(FIXTURE_TREE)])
        self.assertEqual(code, 0)
        summary = json.loads(buf.getvalue())
        self.assertEqual(summary["family"], "actf")
        self.assertEqual(summary["records"], 2)
        self.assertEqual(summary["excluded"], 1)

    def test_cli_scan_returns_two_on_a_coded_refusal(self):
        err = StringIO()
        with patch("sys.stderr", err):
            code = cli.run(["scan", "/tmp/outputs/raw/actf"])
        self.assertEqual(code, 2)
        self.assertIn(cv.FINDING_RECOVERY_ROOT_UNDER_RAW, err.getvalue())

    def test_scan_lineage_matches_the_reader(self):
        trees = {item.path_key: item for item in lineage.read_recovery_tree(FIXTURE_TREE)}
        kept = records.scan_lineage(trees["actf-r10--fd6829e8acef"])
        self.assertEqual(len(kept), 1)
        self.assertFalse(kept[0].excluded)
        payload = kept[0].as_mapping()
        self.assertEqual(payload["record_kind"], cv.RECORD_KIND)
        self.assertEqual(payload["corpus"], cv.CORPUS)


if __name__ == "__main__":
    unittest.main()
