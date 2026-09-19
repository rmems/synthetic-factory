"""Malformed inputs and changed staged artifacts produce coded refusals."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from pipelines.csv_mill import generate, generate_io
from pipelines.csv_mill._contract import CsvRefusal
from tests.test_csv import COMMITTED, FIXTURE, invoke


class CatalogInputBoundaries(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.catalog = self.root / "catalog"
        shutil.copytree(COMMITTED, self.catalog)
        self.meta = json.loads((self.catalog / "CATALOG.json").read_text())

    def _save_rows(self, payload):
        (self.catalog / "plants.jsonl").write_bytes(payload)
        self.meta["plants_sha256"] = hashlib.sha256(payload).hexdigest()
        (self.catalog / "CATALOG.json").write_text(json.dumps(self.meta))

    def _assert_refusal(self, arguments, code):
        status, out, err = invoke([*arguments, "--catalog", str(self.catalog), "--json"])
        self.assertEqual((status, err), (2, ""))
        self.assertEqual(json.loads(out)["code"], code)
        self.assertFalse((self.root / "run").exists())

    def test_catalog_base_and_effective_rounds_are_bounded(self):
        rows = [json.loads(line) for line in (COMMITTED / "plants.jsonl").read_text().splitlines()]
        for base in (10 ** 4096, 10 ** 4096 - 1):
            with self.subTest(base_digits=len(str(base))):
                mill_id = f"csv_r{base}"
                self.meta["mills"][0].update(base_round=base, mill_id=mill_id)
                for row in rows:
                    row.update(base_round=base, mill_id=mill_id, plant_id=f"{mill_id}:{row['slug']}")
                self._save_rows(("\n".join(json.dumps(row) for row in rows) + "\n").encode())
                for selector in (["catalog-check"], ["generate", "--all", "--out", str(self.root / "run")],
                                 ["generate", "--mill", mill_id, "--out", str(self.root / "run")]):
                    self._assert_refusal(selector, "CATALOG_FIELD_INVALID" if base == 10 ** 4096 else "PLANT_FIELD_INVALID")

    def test_deep_jsonl_field_is_a_coded_refusal(self):
        payload = (self.catalog / "plants.jsonl").read_bytes()
        payload = payload.replace(b"{", b'{"extra":' + b"[" * 2000 + b"0" + b"]" * 2000 + b",", 1)
        self._save_rows(payload)
        # Exercise the stdlib fallback: Python 3.14's C scanner is iterative.
        with patch.object(json.scanner, "make_scanner", json.scanner.py_make_scanner):
            self._assert_refusal(["catalog-check"], "CATALOG_FIELD_INVALID")

    def test_catalog_rows_must_preserve_the_declared_index_order(self):
        lines = (self.catalog / "plants.jsonl").read_bytes().splitlines()
        self._save_rows(b"\n".join(reversed(lines)) + b"\n")
        self._assert_refusal(["catalog-check"], "CATALOG_FIELD_INVALID")

    def test_surrogateescaped_unknown_argument_is_a_json_refusal(self):
        status, out, err = invoke(["catalog-check", "--json", "--unknown-\udcff"])
        self.assertEqual((status, err), (2, ""))
        refusal = json.loads(out)
        self.assertEqual(refusal["code"], "USAGE")
        self.assertIn("\\udcff", refusal["message"])
        out.encode("utf-8")


class StagePublicationBoundaries(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.destination = self.root / "run"

    def _run(self):
        return generate.run(generate.GenerateRequest(FIXTURE, self.destination, all_plants=True))

    def _refuse_changed_stage(self, mutate):
        publish = generate_io._publish

        def change(parent, staged, destination, *args):
            mutate(staged)
            return publish(parent, staged, destination, *args)

        with patch.object(generate_io, "_publish", change), self.assertRaises(CsvRefusal) as caught:
            self._run()
        self.assertEqual(caught.exception.code, "DESTINATION_INVALID")
        self.assertFalse(self.destination.exists())
        return next(self.root.glob(".csv-stage-*"))

    def test_extra_entry_refuses_publication_and_survives_cleanup(self):
        stage = self._refuse_changed_stage(lambda path: (path / "foreign").write_text("preserve"))
        self.assertEqual([path.name for path in stage.iterdir()], ["foreign"])
        self.assertEqual((stage / "foreign").read_text(), "preserve")

    def test_replaced_file_refuses_publication_and_survives_cleanup(self):
        def replace(stage):
            (stage / "records.jsonl").unlink()
            (stage / "records.jsonl").write_text("foreign replacement")

        stage = self._refuse_changed_stage(replace)
        self.assertEqual([path.name for path in stage.iterdir()], ["records.jsonl"])
        self.assertEqual((stage / "records.jsonl").read_text(), "foreign replacement")

    def test_same_inode_same_length_edit_is_not_published_or_deleted(self):
        def edit(stage):
            target = stage / "records.jsonl"
            before = target.stat()
            content = target.read_bytes()
            target.write_bytes(b"!" + content[1:])
            self.assertEqual(target.stat().st_ino, before.st_ino)

        stage = self._refuse_changed_stage(edit)
        self.assertEqual([path.name for path in stage.iterdir()], ["records.jsonl"])
        self.assertTrue((stage / "records.jsonl").read_bytes().startswith(b"!"))

    def test_missing_file_refuses_publication(self):
        publish = generate_io._publish

        def remove(parent, staged, destination, *args):
            (staged / "RUN.json").unlink()
            return publish(parent, staged, destination, *args)

        with patch.object(generate_io, "_publish", remove), self.assertRaises(CsvRefusal):
            self._run()
        self.assertEqual(list(self.root.iterdir()), [])

    def test_safe_parent_relocation_reports_final_verified_location(self):
        original = generate_io._OwnedStage.write
        safe = self.root / "safe"
        safe.mkdir()
        alias = self.root / "alias"
        alias.symlink_to(safe, target_is_directory=True)
        relocated = self.root / "relocated"
        self.destination = alias / "run"

        def write(stage, name, payload):
            original(stage, name, payload)
            if name == "RUN.json":
                safe.rename(relocated)
                alias.unlink()
                alias.symlink_to(relocated, target_is_directory=True)

        with patch.object(generate_io._OwnedStage, "write", write):
            summary = self._run()
        self.assertEqual(summary["published_destination"], str(relocated / "run"))
        records = (relocated / "run/records.jsonl").read_bytes()
        self.assertEqual(hashlib.sha256(records).hexdigest(), summary["records_sha256"])

    def _fail_stage_open(self, mutate):
        original = os.open

        def open_stage(path, *args, **kwargs):
            if Path(path).name.startswith(".csv-stage-"):
                mutate(Path(path))
                raise OSError("injected stage open failure")
            return original(path, *args, **kwargs)

        with patch.object(os, "open", open_stage), self.assertRaisesRegex(CsvRefusal, "stage open failure"):
            self._run()

    def test_failed_stage_open_removes_the_authenticated_empty_directory(self):
        self._fail_stage_open(lambda path: None)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_failed_opened_stage_verification_closes_descriptor_and_cleans_directory(self):
        opened = []
        original_open, original_fstat = os.open, os.fstat

        def open_stage(path, *args, **kwargs):
            descriptor = original_open(path, *args, **kwargs)
            if Path(path).name.startswith(".csv-stage-"):
                opened.append(descriptor)
            return descriptor

        def fstat(descriptor):
            if descriptor in opened:
                raise OSError("injected opened stage verification failure")
            return original_fstat(descriptor)

        with patch.object(os, "open", open_stage), patch.object(os, "fstat", fstat):
            with self.assertRaisesRegex(CsvRefusal, "opened stage verification failure"):
                self._run()
        self.assertEqual(len(opened), 1)
        with self.assertRaises(OSError):
            os.fstat(opened[0])
        self.assertEqual(list(self.root.iterdir()), [])

    def test_failed_stage_open_preserves_a_replacement_directory(self):
        def replace(path):
            path.rename(path.parent / "original-stage")
            path.mkdir()
            (path / "foreign").write_text("preserve")

        self._fail_stage_open(replace)
        self.assertEqual(next(self.root.glob(".csv-stage-*/foreign")).read_text(), "preserve")

    def test_failed_stage_open_preserves_an_empty_replacement(self):
        def replace(path):
            path.rename(path.parent / "original-stage")
            path.mkdir()

        self._fail_stage_open(replace)
        self.assertEqual(list(next(self.root.glob(".csv-stage-*")).iterdir()), [])

    def test_partial_write_failure_cleans_only_the_written_bytes_and_allows_retry(self):
        original = os.write
        calls = []

        def write(descriptor, payload):
            if calls:
                raise OSError("injected partial write failure")
            calls.append(descriptor)
            return original(descriptor, payload[:7])

        with patch.object(os, "write", write), self.assertRaisesRegex(CsvRefusal, "partial write"):
            self._run()
        self.assertEqual(list(self.root.iterdir()), [])
        summary = self._run()
        records = (self.destination / "records.jsonl").read_bytes()
        persisted = json.loads((self.destination / "RUN.json").read_text())
        self.assertEqual(hashlib.sha256(records).hexdigest(), summary["records_sha256"])
        self.assertEqual(summary["records_sha256"], persisted["records_sha256"])


if __name__ == "__main__":
    unittest.main()
