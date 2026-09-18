"""Review regressions for catalog provenance and output refusals."""

import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from pipelines.csv_mill import catalog, generate, generate_io
from pipelines.csv_mill._contract import CsvRefusal, FACTORY, RECORD_PREFIX
from tests.test_csv import COMMITTED, TINY_PAIR, _dict_source, invoke


class CatalogBoundaries(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name) / "catalog"
        shutil.copytree(COMMITTED, self.directory)
        self.meta_path = self.directory / "CATALOG.json"
        self.meta = json.loads(self.meta_path.read_text())

    def _save(self, rows=None):
        if rows is not None:
            payload = "".join(json.dumps(row) + "\n" for row in rows).encode()
            (self.directory / "plants.jsonl").write_bytes(payload)
            self.meta["plants_sha256"] = catalog.sha256_bytes(payload)
        self.meta_path.write_text(json.dumps(self.meta))

    def test_source_provenance_cannot_be_removed_or_rewritten(self):
        original = self.meta["source"]
        for source in (None, {**original, "commit": "0" * 40}, {**original, "method": "exec"}):
            with self.subTest(source=source):
                self.meta["source"] = source
                self._save()
                with self.assertRaises(CsvRefusal):
                    catalog.load_catalog(self.directory)

    def test_mill_suffix_must_match_base_round(self):
        self.meta["mills"][0]["mill_id"] = "csv_r999"
        rows = [json.loads(line) for line in (self.directory / "plants.jsonl").read_text().splitlines()]
        for row in rows:
            row["mill_id"] = "csv_r999"
            row["plant_id"] = "csv_r999:" + row["slug"]
        self._save(rows)
        with self.assertRaises(CsvRefusal):
            catalog.load_catalog(self.directory)

    def test_overlapping_mill_rounds_cannot_collide_across_slug_namespaces(self):
        rows = [json.loads(line) for line in (self.directory / "plants.jsonl").read_text().splitlines()]
        first, second = rows[:2]
        first["fail"] = second["slug"]
        second.update(mill_id="csv_r0114", plant_id="csv_r0114:" + second["slug"], index=0)
        self.meta["plant_count"] = 2
        self.meta["mills"] = [
            {**self.meta["mills"][0], "mill_id": row["mill_id"], "plant_count": 1}
            for row in (first, second)
        ]
        self._save([first, second])
        with self.assertRaises(CsvRefusal):
            catalog.load_catalog(self.directory)

    def test_missing_source_identity_pins_are_refused(self):
        for pins in ({}, {"FAC": FACTORY}, {"PREFIX": RECORD_PREFIX}):
            with self.subTest(pins=pins), self.assertRaises(CsvRefusal):
                catalog.plants_from_source(_dict_source([TINY_PAIR], **pins), mill_id="csv_r114", source="unknown.py")

    def test_oversized_mill_suffix_is_a_coded_refusal(self):
        self.meta["mills"][0]["mill_id"] = "csv_r" + "9" * 5000
        self._save()
        with self.assertRaises(CsvRefusal):
            catalog.load_catalog(self.directory)

    def test_plant_source_must_match_its_owning_mill(self):
        rows = [json.loads(line) for line in (self.directory / "plants.jsonl").read_text().splitlines()]
        rows[0]["source"] = "experiments/contradictory-source.py"
        self._save(rows)
        with self.assertRaisesRegex(CsvRefusal, "source"):
            catalog.load_catalog(self.directory)

    def test_mill_and_plant_sources_cannot_jointly_drift_from_pinned_script(self):
        rows = [json.loads(line) for line in (self.directory / "plants.jsonl").read_text().splitlines()]
        for row in rows:
            row["source"] = "experiments/arbitrary.py"
        for mill in self.meta["mills"]:
            mill["source"] = "experiments/arbitrary.py"
        self._save(rows)
        with self.assertRaises(CsvRefusal):
            catalog.load_catalog(self.directory)

    def test_extractor_refuses_invalid_identifier_syntax(self):
        for key, value in (("slug", "bad slug"), ("fail", "bad/fail"), ("ticket", "xls-dn-114")):
            with self.subTest(key=key):
                pair = dict(TINY_PAIR, **{key: value})
                source = _dict_source([pair], FAC=FACTORY, PREFIX=RECORD_PREFIX)
                with self.assertRaises(CsvRefusal):
                    catalog.plants_from_source(source, mill_id="csv_r114", source="recovered.py")

    def test_extractor_translates_an_oversized_numeric_suffix(self):
        source = _dict_source([TINY_PAIR], FAC=FACTORY, PREFIX=RECORD_PREFIX)
        with self.assertRaises(CsvRefusal) as caught:
            catalog.plants_from_source(source, mill_id="csv_r" + "9" * 5000, source="recovered.py")
        self.assertEqual(caught.exception.code, "PLANT_FIELD_INVALID")

    def test_extracted_base_round_must_match_mill_suffix(self):
        source = _dict_source([TINY_PAIR], FAC=FACTORY, PREFIX=RECORD_PREFIX, CATALOG_FIRST=114)
        for mill_id, explicit in (("csv_r999", None), ("csv_r114", 999)):
            with self.subTest(mill_id=mill_id, base=explicit), self.assertRaises(CsvRefusal):
                catalog.plants_from_source(source, mill_id=mill_id, source="recovered.py", base_round=explicit)

    def test_unpaired_surrogate_catalog_text_is_refused_before_generation(self):
        rows = [json.loads(line) for line in (self.directory / "plants.jsonl").read_text().splitlines()]
        rows[0]["domain"] = "bad\ud800text"
        self._save(rows)
        code, out, err = invoke(["generate", "--catalog", str(self.directory), "--all",
                                 "--out", str(self.directory / "run"), "--json"])
        self.assertEqual(code, 2)
        self.assertEqual(err, "")
        self.assertEqual(json.loads(out)["code"], "PLANT_FIELD_MISSING")
        self.assertFalse((self.directory / "run").exists())


class OutputBoundaries(unittest.TestCase):
    def test_parent_file_is_a_structured_refusal(self):
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp) / "file"
            parent.write_text("preserve")
            code, out, err = invoke(["generate", "--all", "--out", str(parent / "run"), "--json"])
            self.assertEqual(code, 2)
            self.assertEqual(err, "")
            self.assertEqual(json.loads(out)["code"], "DESTINATION_INVALID")
            self.assertEqual(parent.read_text(), "preserve")

    def test_staging_write_failure_is_a_single_json_refusal(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "run"
            with patch.object(generate_io._OwnedStage, "write", side_effect=OSError("quota exceeded")):
                code, out, err = invoke(["generate", "--all", "--out", str(destination), "--json"])
            self.assertEqual(code, 2)
            self.assertEqual(err, "")
            self.assertEqual(json.loads(out)["code"], "DESTINATION_INVALID")
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_dangling_destination_is_a_structured_refusal(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "run"
            destination.symlink_to(Path(temp) / "absent")
            code, out, err = invoke(["generate", "--all", "--out", str(destination), "--json"])
            self.assertEqual(code, 2)
            self.assertEqual(err, "")
            self.assertEqual(json.loads(out)["code"], "DESTINATION_EXISTS")
            self.assertTrue(destination.is_symlink())

    def test_failure_domain_and_notes_match_without_a_duplicate_suffix(self):
        plant = catalog.load_catalog(COMMITTED).plants[0]
        record = generate.fail_episode(114, plant, "csv-lll-v1")
        self.assertEqual(record["meta"]["domain"], plant.fail)
        self.assertIn("domain=" + plant.fail, generate.notes_markdown(114, plant))

    def test_abbreviated_json_flags_are_not_supported_parser_spellings(self):
        from pipelines.csv_mill import cli
        for flag in ("--j", "--js"):
            with self.subTest(flag=flag), self.assertRaises(CsvRefusal):
                cli.build_parser().parse_args(["catalog-check", flag])
