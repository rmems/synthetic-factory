"""Stage cleanup retains foreign entries and input bounds return coded refusals."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pipelines.csv_mill import generate, generate_io
from pipelines.csv_mill._contract import CsvRefusal
from tests.test_csv import FIXTURE, FIRST_SLUG, invoke


class StageIntegrity(unittest.TestCase):
    def _request(self, root):
        return generate.GenerateRequest(FIXTURE, root / "run", all_plants=True)

    def test_replaced_stage_is_not_recursively_deleted_on_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            def replace(parent, staged, destination, *args):
                staged.rename(parent / "original-stage")
                staged.mkdir()
                (staged / "foreign").write_text("preserve")
                raise OSError("injected publication failure")
            with patch.object(generate_io, "_publish", replace), self.assertRaises(CsvRefusal):
                generate.run(self._request(root))
            replacement = next(root.glob(".csv-stage-*"))
            self.assertEqual((replacement / "foreign").read_text(), "preserve")
            self.assertEqual(list((root / "original-stage").iterdir()), [])
            self.assertFalse((root / "run").exists())

    def test_unowned_files_inside_original_stage_survive_cleanup(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            def refuse(parent, staged, destination, *args):
                (staged / "foreign").write_text("preserve")
                raise OSError("injected")
            with patch.object(generate_io, "_publish", refuse), self.assertRaises(CsvRefusal):
                generate.run(self._request(root))
            stage = next(root.glob(".csv-stage-*"))
            self.assertEqual([path.name for path in stage.iterdir()], ["foreign"])

    def test_replacement_stage_cannot_be_published(self):
        publish = generate_io._publish
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            def replace(parent, staged, destination, *args):
                staged.rename(parent / "original-stage")
                staged.mkdir()
                (staged / "foreign").write_text("preserve")
                return publish(parent, staged, destination, *args)
            with patch.object(generate_io, "_publish", replace), self.assertRaises(CsvRefusal):
                generate.run(self._request(root))
            self.assertFalse((root / "run").exists())
            self.assertEqual(next(root.glob(".csv-stage-*/foreign")).read_text(), "preserve")


class InputBounds(unittest.TestCase):
    def test_round_outside_exact_integer_domain_is_json_refusal(self):
        with tempfile.TemporaryDirectory() as temp:
            code, out, err = invoke(["generate", "--catalog", str(FIXTURE),
                "--plant", f"csv_r0001:{FIRST_SLUG}", "--round", "1" + "0" * 4096,
                "--out", str(Path(temp) / "run"), "--json"])
            self.assertEqual((code, err), (2, ""))
            self.assertEqual(json.loads(out)["code"], "ROUND_INVALID")
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_catalog_decoder_recursion_is_json_refusal(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "CATALOG.json").write_text("[" * 2000 + "0" + "]" * 2000)
            code, out, err = invoke(["catalog-check", "--catalog", str(root), "--json"])
            self.assertEqual((code, err), (2, ""))
            self.assertEqual(json.loads(out)["code"], "CATALOG_FIELD_INVALID")
