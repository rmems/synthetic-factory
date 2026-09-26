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


    def test_name_replaced_after_first_owned_check_is_preserved(self):
        original = generate_io._StageFile.matches
        replaced = {"done": False}

        def matches(owned, directory, name):
            ok = original(owned, directory, name)
            if ok and name == "records.jsonl" and not replaced["done"]:
                replaced["done"] = True
                target = Path(f"/proc/self/fd/{directory}") / name
                target.unlink()
                target.write_text("replacement")
                return True
            return original(owned, directory, name)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            def refuse(*args, **kwargs):
                raise OSError("injected publication failure")

            with patch.object(generate_io._StageFile, "matches", matches):
                with patch.object(generate_io, "_publish", refuse), self.assertRaises(CsvRefusal):
                    generate.run(self._request(root))
            stage = next(root.glob(".csv-stage-*"))
            self.assertEqual((stage / "records.jsonl").read_text(), "replacement")

    def test_empty_replacement_after_first_identity_check_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "stage"
            path.mkdir()
            identity = generate_io._identity(path.lstat())
            seen = {"n": 0}
            original = Path.lstat

            def lstat(self):
                result = original(self)
                if self == path:
                    seen["n"] += 1
                    if seen["n"] == 1:
                        path.rmdir()
                        path.mkdir()
                        (path / "foreign").write_text("preserve")
                return result

            with patch.object(Path, "lstat", lstat):
                generate_io._remove_empty_entry(path, identity)
            self.assertEqual((path / "foreign").read_text(), "preserve")


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
