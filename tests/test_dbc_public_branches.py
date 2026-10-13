"""DBC public surface: catalog pin refusals, source lookup, and AST extract fall-throughs.

Catalog cases load a mutated copy of ``pipelines/dbc/CATALOG.json`` from a temp
dir (the deferred ``pairs.jsonl`` stays the committed, digest-pinned file);
extract cases feed small in-memory mill sources to ``extract_mill_catalog``.
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
    edited,
    refusal,
    setter,
    write_tree,
)

sys.path.insert(0, str(PIPELINES))

from dbc import catalog_ast, catalog_extract, sources, vocabulary
from dbc.catalog import load_catalog, load_pairs_jsonl

PACKAGE = PIPELINES / "dbc"
COMMITTED = json.loads((PACKAGE / "CATALOG.json").read_text(encoding="utf-8"))
MILL_IDS = tuple(COMMITTED["mills"])
SLICE = vocabulary.SLICE_MILL_ID
BEFORE = MILL_IDS[0]
AFTER = MILL_IDS[MILL_IDS.index(SLICE) + 1]
MILL_PATH = "experiments/dbc-mill-r9.py"
NO_CATALOG = f"{MILL_PATH} has no extractable DBC catalog assignment"
EMPTY_IDENTITY = {
    "success_slug": None,
    "fail_slug": None,
    "success_plant": None,
    "fail_plant": None,
    "fail_handoff": True,
}


def _shift_rows(first, second):
    """Move one row of width from ``second`` to ``first``; the catalog total holds."""

    def edit(document):
        document = edited(
            document, ("mills", first, "n_rows"), COMMITTED["mills"][first]["n_rows"] + 1
        )
        return edited(
            document, ("mills", second, "n_rows"), COMMITTED["mills"][second]["n_rows"] - 1
        )

    return edit


def _extra_mill(document):
    row = dict(COMMITTED["mills"][BEFORE], mill_id="dbc-mill-r0")
    return edited(document, ("mills", "dbc-mill-r0"), row)


class CatalogPinRefusals(unittest.TestCase):
    def _refuse(self, cases):
        built = []
        for edit, fragment in cases:
            directory = write_tree(self, {"CATALOG.json": json.dumps(edit(COMMITTED))})
            built.append((directory / "CATALOG.json", fragment))
        assert_each_refused(self, ValueError, load_catalog, built)

    def test_header_drift_is_refused(self):
        self._refuse(
            (
                (
                    setter("schema", "other"),
                    f"schema is not {vocabulary.CATALOG_SCHEMA_ID}",
                ),
                (
                    setter("preserve_commit", "0" * 40),
                    "preserve_commit drifted from vocabulary",
                ),
                (
                    setter("factory", "other"),
                    "factory/generator drifted from vocabulary",
                ),
                (
                    setter("generator", "other"),
                    "factory/generator drifted from vocabulary",
                ),
                (setter("slice", "r0"), "slice drifted from vocabulary"),
            )
        )

    def test_mill_set_drift_is_refused(self):
        self._refuse(
            (
                (
                    setter("mills", BEFORE, DELETE),
                    f"pairs.jsonl names unknown mill {BEFORE}",
                ),
                (_extra_mill, "pairs.jsonl missing deferred mills: ['dbc-mill-r0']"),
                (
                    setter("mills", SLICE, DELETE),
                    f"catalog mills drifted from sources: extra=[] missing=['{SLICE}']",
                ),
                (
                    setter("mills", BEFORE, "pairs", COMMITTED["mills"][SLICE]["pairs"][:1]),
                    f"{BEFORE} is not the first slice and must omit CATALOG pair rows",
                ),
            )
        )

    def test_width_drift_is_refused(self):
        slice_pairs = COMMITTED["mills"][SLICE]["pairs"]
        self._refuse(
            (
                (
                    setter("mills", BEFORE, "n_rows", COMMITTED["mills"][BEFORE]["n_rows"] + 1),
                    f"catalog n_pair_rows drifted from {vocabulary.N_PAIR_ROWS}",
                ),
                (
                    setter("mills", SLICE, "pairs", slice_pairs[:-1]),
                    "r193 slice n_rows does not match extracted pairs",
                ),
                (_shift_rows(SLICE, AFTER), "r193 slice n_rows does not match extracted pairs"),
                (_shift_rows(BEFORE, AFTER), f"{BEFORE} deferred pairs drifted from n_rows"),
            )
        )

    def test_deferred_identity_drift_is_refused(self):
        self._refuse(
            (
                (
                    setter("mills", BEFORE, "first_slug", "x"),
                    f"{BEFORE} first_slug drifted from pairs.jsonl",
                ),
                (
                    setter("mills", BEFORE, "last_slug", "x"),
                    f"{BEFORE} last_slug drifted from pairs.jsonl",
                ),
                (
                    setter("mills", BEFORE, "mill_id", "dbc-mill-rX"),
                    "dbc-mill-rX mill_id drifted from pairs.jsonl",
                ),
            )
        )

    def test_a_drifted_pairs_file_is_refused_by_its_vocabulary_digest(self):
        payload = (PACKAGE / "pairs.jsonl").read_bytes().replace(b"-cache", b"-cachf", 1)
        path = write_tree(self, {"pairs.jsonl": payload}) / "pairs.jsonl"
        with refusal(self, ValueError, "sha256 drifted from vocabulary"):
            load_pairs_jsonl(path)


class SourceLookup(unittest.TestCase):
    def test_slug_sources_are_the_slug_listing_pins(self):
        kinds = {source.kind for source in sources.slug_sources()}
        self.assertLessEqual(kinds, {vocabulary.KIND_SLUGS})

    def test_a_known_mill_id_resolves_to_its_pin(self):
        self.assertEqual(sources.source_by_id(SLICE).mill_id, SLICE)

    def test_an_unknown_mill_id_is_refused(self):
        with refusal(self, KeyError, "unknown dbc mill source 'dbc-mill-r0'"):
            sources.source_by_id("dbc-mill-r0")


class ExtractFallThroughs(unittest.TestCase):
    def _extract(self, text):
        return catalog_extract.extract_mill_catalog(text, path=MILL_PATH)

    def test_sources_without_a_catalog_shape_are_refused(self):
        cases = (
            ("obj.attr = 1\n", NO_CATALOG),
            ("PAIRS = [1]\n", NO_CATALOG),
            ("PAIRS = [({'slug': 'a'}, other())]\n", NO_CATALOG),
        )
        assert_each_refused(self, ValueError, self._extract, cases)

    def test_zip_tables_read_dict_rows(self):
        text = (
            "_LANGS = [{'slug': 'a'}]\n_LEFTS = [{'slug': 'b'}]\n"
            "PAIRS = [(x, y) for x, y in zip(_LANGS, _LEFTS)]\n"
        )
        record = self._extract(text)
        self.assertEqual((record["shape"], record["first_slug"]), ("pairs-zip-tables", "a"))
        self.assertEqual(record["pairs"][0]["fail_slug"], "b")

    def test_a_non_literal_mixed_arm_keeps_an_empty_success_identity(self):
        record = self._extract("PAIRS = [({'slug': 'a'}, suc('b')), ({'slug': name}, suc('c'))]\n")
        self.assertEqual(record["shape"], "pairs-ctor")
        self.assertEqual(
            (record["pairs"][1]["success_slug"], record["pairs"][1]["fail_slug"]), (None, "c")
        )

    def test_a_non_literal_dict_pair_keeps_an_empty_identity(self):
        record = self._extract(
            "PAIRS = [({'slug': 'a'}, {'slug': 'b'}), ({'slug': name}, {'slug': 'c'})]\n"
        )
        self.assertEqual(record["shape"], "pairs-literal")
        self.assertEqual(record["pairs"][1], EMPTY_IDENTITY)

    def test_composing_no_companion_records_is_a_no_op(self):
        self.assertEqual(catalog_extract.compose_family_records({}), {})


class DbcSharedSurface(SharedExtractSurfaceCases, unittest.TestCase):
    ast_module = catalog_ast
    extract_module = catalog_extract

    def test_first_joined_list_path_skips_a_list_without_a_path_head(self):
        source = "LOOPS = [name]\nLOOPS = [ROOT / 'experiments' / 'dbc-loop-r1.py']\n"
        self.assertEqual(
            catalog_ast.extract_first_joined_list_path(source, "LOOPS"),
            "experiments/dbc-loop-r1.py",
        )


if __name__ == "__main__":
    unittest.main()
