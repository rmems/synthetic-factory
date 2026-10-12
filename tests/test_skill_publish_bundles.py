"""build_bundles.py fails closed: each converted check refuses, and a good tree builds.

Also drives build_bundles -> build_fix end to end on one fixture tree. Offline: the
module roots are patched to scratch trees and pyarrow is a stand-in (see
skill_publish_test_support).
"""

import importlib
import json
import shutil
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
support = importlib.import_module("skill_publish_test_support")

FACTORY = support.FACTORY
NAME = support.NAME
jsonl = support.jsonl
record = support.record


class BuildBundlesTests(support.ScriptChecks, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.bb = support.script("build_bundles")
        self.error = self.bb.BundleCheckError
        self.source = self.write_source_tree()
        self.run_dir = self.write_bundle_inputs(self.source)
        self.enterContext(mock.patch.multiple(self.bb, **self.bundle_roots()))
        self.enterContext(support.installed_pyarrow(*support.fake_pyarrow()))
        self.cfg = self.bb.FACTORIES[0]
        self.bundle = self.tmp / "bundles" / NAME

    def test_build_one_accepts_a_consistent_fixture(self):
        summary = self.bb.build_one(self.cfg)

        self.assertEqual(summary["rounds"], ["r01", "r02c"])
        self.assertEqual(summary["superseded"], ["batch-r02.jsonl"])
        self.assertEqual(summary["records"], 4)
        self.assertEqual(summary["decisions"], {"ACCEPT": 1})
        self.assertEqual(
            (self.bundle / "data/raw/batch-r02c.jsonl").read_bytes(),
            (self.source / "batch-r02c.jsonl").read_bytes(),
        )
        support.rights_document.load_rights_document_bytes(
            (self.bundle / "rights.json").read_bytes()
        )
        self.assertIn("indexes 4 rows.", (self.bundle / "README.md").read_text())

    def test_round_key_refuses_an_unparseable_name(self):
        self.assert_refuses(self.error, "batch-final.jsonl", self.bb.round_key, "batch-final.jsonl")

    def test_round_files_refuses_a_batch_name_outside_the_c_suffix_rule(self):
        (self.run_dir / "batch-r03b.jsonl").write_bytes(b"")
        self.assert_refuses(
            self.error,
            str(["batch-r01.jsonl", "batch-r02c.jsonl", "batch-r03b.jsonl"]),
            self.bb._round_files,
            self.run_dir,
        )

    def test_copy_batches_refuses_drift_from_the_immutable_source(self):
        (self.run_dir / "batch-r01.jsonl").write_bytes(jsonl(record("t-r01-0")))
        self.assert_refuses(
            self.error, "drift vs immutable source: batch-r01.jsonl", self.bb.build_one, self.cfg
        )

    def test_copy_batches_refuses_a_copy_that_does_not_read_back(self):
        self.bb._reset_bundle_dirs(self.bundle)
        with mock.patch.object(Path, "write_bytes", lambda path, data: path.write_text("x")):
            self.assert_refuses(
                self.error,
                "raw copy does not read back byte-identical: batch-r01.jsonl",
                self.bb._copy_batches, FACTORY, self.run_dir, self.bundle, ["batch-r01.jsonl"],
            )

    def test_copy_batches_refuses_a_lossy_line_split(self):
        self.bb._reset_bundle_dirs(self.bundle)
        first_line = jsonl(record("t-r01-0")).decode().rstrip("\n")
        with mock.patch.object(
            support.strict_jsonl, "strict_lf_jsonl_lines", return_value=[first_line]
        ):
            self.assert_refuses(
                self.error, "batch-r01.jsonl", self.bb._copy_batches,
                FACTORY, self.run_dir, self.bundle, ["batch-r01.jsonl"],
            )

    def test_copy_notes_refuses_drift_from_the_immutable_source(self):
        self.bb._reset_bundle_dirs(self.bundle)
        (self.run_dir / "NOTES-r01.md").write_bytes(b"edited\n")
        self.assert_refuses(
            self.error, "drift vs immutable source: NOTES-r01.md", self.bb._copy_notes,
            FACTORY, self.run_dir, self.bundle, ["NOTES-r01.md"],
        )

    def test_viewer_checks_refuse_each_projection_defect(self):
        support.assert_viewer_defects_refused(self, self.bb, self.error, local_import=True)

    def test_census_refuses_repeated_or_non_string_ids(self):
        for records in ([record("a"), record("a")], [record(7)]):
            with self.subTest(records=records):
                self.assert_refuses(self.error, "ids not unique", self.bb._record_census, records)

    def test_stamp_checks_refuse_each_foreign_stamp(self):
        support.assert_stamp_defects_refused(self, self.bb._check_record_stamps, self.error)

    def test_superseded_base_must_exist_in_the_immutable_source(self):
        (self.source / "batch-r02.jsonl").unlink()
        self.assert_refuses(
            self.error, "batch-r02.jsonl", self.bb._superseded_bases, FACTORY, ["batch-r02c.jsonl"]
        )

    def test_release_status_refuses_a_sibling_key_order_drift(self):
        self.bb._reset_bundle_dirs(self.bundle)
        reordered = dict.fromkeys(reversed(support.STATUS_KEYS), "x")
        sibling_status = self.tmp / "siblings" / support.SIBLING_NAME / "release-status.json"
        sibling_status.write_text(json.dumps(reordered))
        self.assert_refuses(
            self.error,
            str((list(support.STATUS_KEYS), list(reordered))),
            self.bb._write_release_status, self.bundle, self.cfg,
        )


class BundleToFixEndToEndTests(support.ScriptChecks, unittest.TestCase):
    """build_bundles output, staged as the current Hub state, drives build_fix end to end."""

    def test_delta_bundle_adds_the_omitted_base_file(self):
        bb, bf = support.script("build_bundles"), support.script("build_fix")
        self.write_bundle_inputs(self.write_source_tree())
        with mock.patch.multiple(bb, **self.bundle_roots()), support.installed_pyarrow(
            *support.fake_pyarrow()
        ):
            bb.build_one(bb.FACTORIES[0])
        current = self.tmp / "current" / NAME
        shutil.copytree(self.tmp / "bundles" / NAME, current)
        card = (current / "README.md").read_text()
        research_card = card.replace("license: cc-by-nc-4.0\n", support.RESEARCH_LICENSE)
        (current / "README.md").write_text(research_card)

        with mock.patch.multiple(
            bf, SOURCE=self.tmp / "source", CURRENT=self.tmp / "current",
            FIX=self.tmp / "fix", RUN_FIX=self.tmp / "run-fix",
        ):
            summary = bf.build_one(FACTORY, support.REPO_ID, ["batch-r02.jsonl"])

        self.assertEqual(summary["added_files"], ["data/raw/batch-r02.jsonl"])
        self.assertEqual((summary["records_before"], summary["records_after"]), (4, 5))
        self.assertEqual(summary["rounds_after"], ["r01", "r02", "r02c"])
        self.assertEqual(
            summary["delta_files"],
            ["README.md", "data/raw/batch-r02.jsonl", "data/viewer/records.parquet",
             "provenance.json", "rights.json"],
        )
        self.assertEqual(
            sorted(p.name for p in (self.tmp / "run-fix" / FACTORY).iterdir()),
            ["batch-r01.jsonl", "batch-r02.jsonl", "batch-r02c.jsonl"],
        )


if __name__ == "__main__":
    unittest.main()
