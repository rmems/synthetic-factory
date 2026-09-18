"""CSV output cannot enter raw evidence through a replaced parent alias."""

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pipelines.csv_mill import generate, generate_io
from pipelines.csv_mill._contract import CsvRefusal
from tests.test_csv import FIXTURE


class ParentBinding(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.raw = self.root / "outputs/raw"
        self.raw.mkdir(parents=True)
        self.safe = self.root / "safe"
        self.safe.mkdir()
        self.alias = self.root / "alias"
        self.alias.symlink_to(self.safe, target_is_directory=True)

    def _retarget(self):
        self.alias.unlink()
        self.alias.symlink_to(self.raw, target_is_directory=True)

    def _run(self, destination):
        return generate.run(generate.GenerateRequest(FIXTURE, destination, all_plants=True))

    def test_alias_replaced_after_preflight_cannot_write_raw(self):
        original = generate.write_run_files

        def replace(*args):
            self._retarget()
            return original(*args)

        with patch.object(generate, "write_run_files", replace), self.assertRaises(CsvRefusal):
            self._run(self.alias / "run")
        self.assertEqual(list(self.raw.iterdir()), [])

    def test_missing_parent_replaced_by_symlink_during_creation_is_refused(self):
        original = os.mkdir

        def replace(path, *args, **kwargs):
            if Path(path).name == "missing":
                (self.safe / "missing").symlink_to(self.raw, target_is_directory=True)
            return original(path, *args, **kwargs)

        with patch.object(os, "mkdir", replace), self.assertRaises(CsvRefusal):
            self._run(self.safe / "missing/run")
        self.assertEqual(list(self.raw.iterdir()), [])

    def test_alias_retarget_before_publication_cannot_report_success(self):
        original = generate_io._publish

        def replace(*args):
            self._retarget()
            return original(*args)

        with patch.object(generate_io, "_publish", replace), self.assertRaises(CsvRefusal):
            self._run(self.alias / "run")
        self.assertEqual(list(self.raw.iterdir()), [])

    def test_stable_parent_alias_can_create_nested_output(self):
        self._run(self.alias / "nested/run")
        self.assertEqual(len(list((self.safe / "nested/run").iterdir())), 3)
        self.assertEqual(list(self.raw.iterdir()), [])

    def test_alias_retarget_after_commit_reports_the_anchored_output(self):
        original = generate_io.rename_noreplace

        def publish(*args):
            original(*args)
            self._retarget()

        with patch.object(generate_io, "rename_noreplace", publish):
            summary = self._run(self.alias / "run")
        self.assertEqual(summary["published_destination"], str(self.safe / "run"))
        self.assertEqual(len(list((self.safe / "run").iterdir())), 3)
        self.assertEqual(list(self.raw.iterdir()), [])

    def test_foreign_replacement_after_commit_is_never_removed(self):
        original = generate_io.rename_noreplace

        def publish(*args):
            original(*args)
            (self.safe / "run").rename(self.safe / "retained-run")
            (self.safe / "run").mkdir()
            (self.safe / "run/foreign").write_text("preserve")
            self._retarget()

        with patch.object(generate_io, "rename_noreplace", publish):
            self._run(self.alias / "run")
        self.assertEqual((self.safe / "run/foreign").read_text(), "preserve")
        self.assertEqual(len(list((self.safe / "retained-run").iterdir())), 3)
        self.assertEqual(list(self.raw.iterdir()), [])

    def test_alias_retarget_on_final_staging_write_refuses_before_rename(self):
        original = Path.write_text

        def write(path, *args, **kwargs):
            result = original(path, *args, **kwargs)
            if path.name == "RUN.json":
                self._retarget()
            return result

        with patch.object(Path, "write_text", write), self.assertRaises(CsvRefusal):
            self._run(self.alias / "run")
        self.assertEqual(list(self.safe.iterdir()), [])
        self.assertEqual(list(self.raw.iterdir()), [])
