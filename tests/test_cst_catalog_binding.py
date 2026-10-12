"""Pin ``cst`` catalog pin binding and the joined-path constant reader."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from cst.catalog import load_catalog
from cst.catalog_extract import extract_joined_path_constant, extract_mill_catalog

_CATALOG = json.loads((REPO / "pipelines" / "cst" / "CATALOG.json").read_text(encoding="utf-8"))
_FIRST = next(iter(_CATALOG["mills"]))


class CatalogPinTests(unittest.TestCase):
    def _refusal(self, mutate) -> str:
        document = copy.deepcopy(_CATALOG)
        mutate(document["mills"][_FIRST])
        with tempfile.TemporaryDirectory(prefix="cst-binding-") as td:
            path = Path(td) / "CATALOG.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaises(ValueError) as caught:
                load_catalog(path)
        return str(caught.exception)

    def test_path_blob_and_kind_must_match_the_source_pin(self):
        for key, value in (("path", "x.py"), ("blob_sha", "0" * 40), ("kind", "plants")):
            with self.subTest(key=key):
                message = self._refusal(lambda mill, key=key, value=value: mill.update({key: value}))
                self.assertEqual(message, f"{_FIRST} pin disagrees with sources.py")

    def test_row_count_must_match_the_extracted_rows(self):
        message = self._refusal(lambda mill: mill.update(n_rows=mill["n_rows"] + 1))
        self.assertEqual(message, f"{_FIRST} n_rows does not match extracted rows")


class JoinedPathConstantTests(unittest.TestCase):
    def test_only_a_division_by_a_string_literal_is_read(self):
        source = (
            "MILL_PATH = 1\n"
            "x.MILL_PATH = ROOT / 'ignored.py'\n"
            "MILL_PATH = ROOT + 'nope.py'\n"
            "MILL_PATH = ROOT / NAME\n"
            "MILL_PATH = ROOT / 'experiments/cst-mill-r1414.py'\n"
        )
        self.assertEqual(extract_joined_path_constant(source, "MILL_PATH"), "experiments/cst-mill-r1414.py")
        self.assertIsNone(extract_joined_path_constant("MILL_PATH = ROOT / NAME\n", "MILL_PATH"))


class MillRecordRefusalTests(unittest.TestCase):
    def test_pairs_and_plants_shapes_are_refused_with_the_path(self):
        path = "experiments/cst-mill-r9999.py"
        cases = (
            ("CATALOG_FIRST = 4\nPAIRS = []\n", f"{path}: PAIRS is empty"),
            ("CATALOG_FIRST = 4\nPAIRS = [(1, 's'), (1, 's', 3)]\n", f"{path}: mixed PAIRS arities [2, 3]"),
            ("CATALOG_FIRST = 'a'\nPAIRS = [(1, 's')]\n", f"{path}: CATALOG_FIRST must be an int"),
            ("PLANTS = []\n", f"{path}: PLANTS is empty"),
            ("PLANTS = [1]\n", f"{path}: PLANTS[0] is not a dict"),
            ("X = 1\n", f"{path} has no PAIRS or PLANTS catalog assignment"),
        )
        for source, message in cases:
            with self.subTest(message=message), self.assertRaises(ValueError) as caught:
                extract_mill_catalog(source, path=path)
            self.assertEqual(str(caught.exception), message)

    def test_pairs_record_carries_the_source_identity(self):
        record = extract_mill_catalog(
            "CATALOG_FIRST = 4\nPAIRS = [(1, 'first'), (2, 'last')]\n",
            path="experiments/cst-mill-r9999.py",
            blob_sha="b" * 40,
        )
        self.assertEqual(
            (record["mill_id"], record["blob_sha"], record["n_rows"], record["first_slug"], record["last_slug"]),
            ("cst-mill-r9999", "b" * 40, 2, "first", "last"),
        )


if __name__ == "__main__":
    unittest.main()
