"""AZR public surface: catalog pin refusals, pair-file framing, and AST extract refusals.

Catalog cases load a mutated copy of ``pipelines/azr/CATALOG.json`` next to a
copy of its ``pairs.jsonl`` in a temp dir; extract cases feed small in-memory
mill and plant sources to ``extract_mill_catalog`` / ``extract_plant_catalog``.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mill_catalog_public_support import (
    DELETE,
    PIPELINES,
    SharedExtractSurfaceCases,
    assert_each_refused,
    compact,
    edited,
    parse_expr,
    read_jsonl,
    refusal,
    setter,
    write_tree,
)

sys.path.insert(0, str(PIPELINES))

from azr import catalog_ast, catalog_extract, vocabulary
from azr.catalog import load_catalog

PACKAGE = PIPELINES / "azr"
COMMITTED = json.loads((PACKAGE / "CATALOG.json").read_text(encoding="utf-8"))
PAIRS_TEXT = (PACKAGE / "pairs.jsonl").read_text(encoding="utf-8")
FIRST_PAIR_ROW = read_jsonl(PACKAGE / "pairs.jsonl")[0]
SLICE = vocabulary.SLICE_MILL_ID
BULKY = vocabulary.BULKY_MILL_ID
DEFERRED = next((mill for mill in COMMITTED["mills"] if mill not in {SLICE, BULKY}), None)
MILL_PATH = "experiments/azr-mill-r9.py"
PLANT_PATH = "experiments/azr-plants-r9.py"
NONE_IDENTITY = {
    "success_slug": None,
    "fail_slug": None,
    "success_plant": None,
    "fail_plant": None,
    "fail_handoff": False,
}
ZIP_MILL = (
    "_spec = importlib.util.spec_from_file_location('p', EXPERIMENTS / 'azr-plants-r9.py')\n"
    "if PAIRS[0][0]['slug'] != {success!r}:\n    raise SystemExit(1)\n"
    "if PAIRS[0][1]['slug'] != {fail!r}:\n    raise SystemExit(1)\n"
)
ZIP_PLANT = "EXTRA_IDOR_ROWS = [dict(slug='x1')]\nBFLA_ROWS = [dict(slug='y1')]\n"
UNEVEN_PLANT = "EXTRA_IDOR_ROWS = [dict(slug='a'), dict(slug='b')]\nBFLA_ROWS = [dict(slug='c')]\n"


def _rows(mill_id, delta):
    return lambda d: edited(
        d, ("mills", mill_id, "n_rows"), COMMITTED["mills"][mill_id]["n_rows"] + delta
    )


def _bulky_narrower(document):
    return _rows(DEFERRED, 1)(_rows(BULKY, -1)(document))


def _plant(text):
    return catalog_extract.extract_plant_catalog(text, path=PLANT_PATH)


def _mill(text, plants=None):
    return catalog_extract.extract_mill_catalog(text, path=MILL_PATH, plants=plants)


class CatalogPinRefusals(unittest.TestCase):
    def _catalog(self, document=None, pairs_text=PAIRS_TEXT) -> Path:
        document = COMMITTED if document is None else document
        files = {"CATALOG.json": json.dumps(document), "pairs.jsonl": pairs_text}
        return write_tree(self, files) / "CATALOG.json"

    def test_header_drift_is_refused(self):
        cases = (
            (("schema",), f"schema is not {vocabulary.CATALOG_SCHEMA_ID}"),
            (("preserve_commit",), "preserve_commit drifted from vocabulary"),
            (("factory",), "factory/generator drifted from vocabulary"),
            (("generator",), "factory/generator drifted from vocabulary"),
            (("slice",), "slice drifted from vocabulary"),
        )
        built = [
            (self._catalog(edited(COMMITTED, path, "other")), message) for path, message in cases
        ]
        assert_each_refused(self, ValueError, load_catalog, built)

    def test_mill_and_width_drift_is_refused(self):
        cases = (
            (
                setter("mills", DEFERRED, DELETE),
                f"catalog mills drifted from sources: extra=[] missing=['{DEFERRED}']",
            ),
            (_rows(SLICE, 1), "r1181 slice n_rows does not match extracted pairs"),
            (_rows(DEFERRED, 1), "deferred pair width drifted from vocabulary"),
            (_bulky_narrower, "r1205 bulky width drifted from vocabulary"),
        )
        built = [(self._catalog(edit(COMMITTED)), message) for edit, message in cases]
        assert_each_refused(self, ValueError, load_catalog, built)

    def test_pairs_naming_the_first_slice_mill_are_refused(self):
        row = dict(FIRST_PAIR_ROW, mill_id=SLICE)
        path = self._catalog(pairs_text=PAIRS_TEXT + compact(row) + "\n")
        with refusal(self, ValueError, "pairs.jsonl must omit the r1181 first-slice mill"):
            load_catalog(path)


class PairFileFraming(unittest.TestCase):
    def test_a_missing_pair_file_is_refused(self):
        path = write_tree(self, {}) / "pairs.jsonl"
        with refusal(self, ValueError, f"cannot load AZR pairs {path}"):
            catalog_extract.load_pair_rows(path)

    def test_a_pair_file_without_a_final_newline_is_refused(self):
        path = write_tree(self, {"pairs.jsonl": PAIRS_TEXT.rstrip("\n")}) / "pairs.jsonl"
        with refusal(self, ValueError, "pairs.jsonl must be LF-framed jsonl"):
            catalog_extract.load_pair_rows(path)


class PlantExtractRefusals(unittest.TestCase):
    def test_plant_catalog_refusals(self):
        cases = (
            (
                "EXTRA_IDOR_ROWS = [dict(plant='p')]\n",
                "catalog row is not a literal slug identity",
            ),
            (
                "EXTRA_IDOR_ROWS = [{'slug': name}]\n",
                "catalog row is not a literal slug identity",
            ),
            ("X = 1\n", f"{PLANT_PATH} has no EXTRA_IDOR_ROWS catalog"),
            (
                UNEVEN_PLANT,
                f"{PLANT_PATH}: idor 2 != bfla 1",
            ),
        )
        assert_each_refused(self, ValueError, _plant, cases)

    def test_dict_literal_rows_are_slug_identities(self):
        record = _plant("EXTRA_IDOR_ROWS = [{'slug': 'x1', 'plant': 'a'}]\n")
        self.assertEqual(
            (record["first_slug"], record["idors"]), ("x1", [{"slug": "x1", "plant": "a"}])
        )


class MillExtractRefusals(unittest.TestCase):
    def test_idor_mill_refusals(self):
        cases = (
            (
                "obj.attr = 1\nIDOR_ROWS = [dict(slug=None)]\n",
                "idor-bfla-rows catalog has no success slugs",
            ),
            (
                "IDOR_ROWS = [dict(slug='a')]\n_load_extra('azr_plants_r9')\n",
                f"{MILL_PATH} needs companion plant {PLANT_PATH}",
            ),
            (
                "IDOR_ROWS = [dict(slug='a'), dict(slug='b')]\ndef _bflas():\n    add(slug='c')\n",
                "IDOR_ROWS 2 != _bflas 1",
            ),
        )
        assert_each_refused(self, ValueError, _mill, cases)

    def test_zip_tips_must_match_the_companion_plant(self):
        cases = (
            (
                ZIP_MILL.format(success="other", fail="y1"),
                f"{MILL_PATH} tip slug other != x1",
            ),
            (ZIP_MILL.format(success="x1", fail="zz"), f"{MILL_PATH} fail tip zz != y1"),
        )
        assert_each_refused(
            self, ValueError, lambda text: _mill(text, {PLANT_PATH: ZIP_PLANT}), cases
        )

    def test_new_pairs_keep_non_pair_entries_as_empty_identities(self):
        record = _mill("NEW_PAIRS = [1, ({'slug': 'a'}, 2)]\n")
        self.assertEqual(record["shape"], vocabulary.SHAPE_NEW_PLUS_KEEP)
        self.assertEqual(record["pairs"][1:], [NONE_IDENTITY, NONE_IDENTITY])


class AzrSharedSurface(SharedExtractSurfaceCases, unittest.TestCase):
    ast_module = catalog_ast
    extract_module = catalog_extract

    def test_identity_kwargs_reads_only_literal_dicts(self):
        literal = catalog_ast.identity_kwargs(parse_expr("{'slug': 'x1', 'plant': 'a'}"))
        self.assertEqual(literal, {"slug": "x1", "plant": "a"})
        self.assertIsNone(catalog_ast.identity_kwargs(parse_expr("{'slug': name}")))


if __name__ == "__main__":
    unittest.main()
