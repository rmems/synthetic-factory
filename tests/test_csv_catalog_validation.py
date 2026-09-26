"""Catalog integrity regressions for the CSV mill."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pipelines.csv_mill import catalog
from pipelines.csv_mill._contract import (
    CsvRefusal,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_SOURCE_NOT_PARSEABLE,
)
from tests.test_csv import COMMITTED, TINY_PAIR, _dict_source


class CatalogValidation(unittest.TestCase):
    def test_duplicate_index_within_mill_is_refused(self):
        """An index collision would make a catalog's round mapping ambiguous."""

        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp) / "catalog"
            shutil.copytree(COMMITTED, directory)
            rows = [
                json.loads(line) for line in (directory / "plants.jsonl").read_text().splitlines()
            ]
            rows[-1]["index"] = rows[0]["index"]
            payload = "".join(json.dumps(row) + "\n" for row in rows)
            (directory / "plants.jsonl").write_text(payload, encoding="utf-8")
            meta_path = directory / "CATALOG.json"
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            meta["plants_sha256"] = catalog.sha256_bytes(payload.encode())
            meta_path.write_text(json.dumps(meta), encoding="utf-8")

            with self.assertRaises(CsvRefusal) as caught:
                catalog.load_catalog(directory)

        self.assertEqual(caught.exception.code, FINDING_CATALOG_FIELD_INVALID)

    def test_duplicate_mill_rows_are_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp) / "catalog"
            shutil.copytree(COMMITTED, directory)
            path = directory / "CATALOG.json"
            meta = json.loads(path.read_text())
            meta["mills"].append(meta["mills"][0])
            path.write_text(json.dumps(meta))
            with self.assertRaises(CsvRefusal) as caught:
                catalog.load_catalog(directory)
        self.assertEqual(caught.exception.code, FINDING_CATALOG_FIELD_INVALID)

    def test_boolean_integer_pins_are_refused(self):
        for key in ("plant_count", "quota_per_round"):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temp:
                directory = Path(temp) / "catalog"
                shutil.copytree(COMMITTED, directory)
                path = directory / "CATALOG.json"
                meta = json.loads(path.read_text())
                meta[key] = True
                path.write_text(json.dumps(meta))
                with self.assertRaises(CsvRefusal) as caught:
                    catalog.load_catalog(directory)
                self.assertEqual(caught.exception.code, FINDING_CATALOG_FIELD_INVALID)

    def test_plants_are_parsed_from_the_authenticated_read(self):
        """A replaced plants file cannot change the parsed bytes after hashing."""

        expected = catalog.load_catalog(COMMITTED)
        original_read_bytes = Path.read_bytes
        original_read_text = Path.read_text
        reads = []

        def read_bytes(path):
            if path.name == "plants.jsonl":
                reads.append(path)
                if len(reads) > 1:
                    return b"changed after hashing\n"
            return original_read_bytes(path)

        def read_text(path, *args, **kwargs):
            if path.name == "plants.jsonl":
                return "changed after hashing\n"
            return original_read_text(path, *args, **kwargs)

        with (
            patch.object(Path, "read_bytes", read_bytes),
            patch.object(Path, "read_text", read_text),
        ):
            loaded = catalog.load_catalog(COMMITTED)
        self.assertEqual(loaded.plants, expected.plants)
        self.assertEqual(len(reads), 1)

    def test_unicode_separators_inside_json_strings_are_data(self):
        from pipelines.csv_mill.catalog_validation import _read_jsonl

        value = {"text": "embedded\u0085next\u2028line\u2029paragraph"}
        payload = (json.dumps(value, ensure_ascii=False) + "\n").encode("utf-8")
        self.assertEqual(_read_jsonl(payload, Path("plants.jsonl")), (value,))

    def test_mill_id_accepts_only_ascii_digits(self):
        source = _dict_source([TINY_PAIR])
        with self.assertRaises(CsvRefusal):
            catalog.plants_from_source(source, mill_id="csv_r١١٤", source="unicode.py")

    def test_repeated_pairs_assignment_is_refused(self):
        """A recovered source must have one unambiguous PAIRS assignment."""

        source = _dict_source([TINY_PAIR]) + _dict_source([TINY_PAIR])
        with self.assertRaises(CsvRefusal) as caught:
            catalog.plants_from_source(source, mill_id="csv_r114", source="duplicate.py")
        self.assertEqual(caught.exception.code, FINDING_SOURCE_NOT_PARSEABLE)


if __name__ == "__main__":
    unittest.main()
