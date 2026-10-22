"""LEF public surface: catalog pin refusals, table extract refusals, and plant-record width.

Catalog cases load a mutated copy of ``pipelines/lef`` (``CATALOG.json``,
``rows.jsonl``, ``plants.jsonl``, ``plants_b.jsonl``) out of a temp dir; extract
cases feed a small six-table mill source to ``extract_mill_catalog``.
"""

from __future__ import annotations

import ast
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mill_catalog_public_support import (
    PIPELINES,
    SharedExtractSurfaceCases,
    assert_each_refused,
    compact,
    edited,
    read_jsonl,
    refusal,
    setter,
    write_tree,
)

sys.path.insert(0, str(PIPELINES))

from lef import catalog_ast, catalog_extract, plants_extract, vocabulary
from lef.catalog import load_catalog

PACKAGE = PIPELINES / "lef"
MEMBERS = ("rows.jsonl", "plants.jsonl", "plants_b.jsonl")
COMMITTED = json.loads((PACKAGE / "CATALOG.json").read_text(encoding="utf-8"))
MILL_IDS = tuple(COMMITTED["mills"])
MILL_PATH = "experiments/lef-mill-r9.py"
TABLE_ROWS = {
    name: tuple(f"{name.lower()}-{index}" for index in range(len(fields)))
    for name, fields in vocabulary.TABLE_FIELDS.items()
}
TABLES_SOURCE = "".join(f"{name} = [{TABLE_ROWS[name]!r}]\n" for name in vocabulary.TABLE_NAMES)
PLANT_APPEND = "PAIRS.append((_ok(slug='a'), _bad(slug='b')))\n"


def _move_rows(document):
    """r629 takes a negative width; r728 absorbs it so the row total still holds."""

    first, second = MILL_IDS[0], MILL_IDS[1]
    shift = COMMITTED["mills"][first]["n_rows"] + 1
    document = edited(document, ("mills", first, "n_rows"), -1)
    return edited(
        document, ("mills", second, "n_rows"), COMMITTED["mills"][second]["n_rows"] + shift
    )


def _extract(text):
    return catalog_extract.extract_mill_catalog(text, path=MILL_PATH)


class CatalogPinRefusals(unittest.TestCase):
    def _catalog(self, document, members=None) -> Path:
        files = {name: (PACKAGE / name).read_bytes() for name in MEMBERS}
        files.update(members or {})
        files["CATALOG.json"] = json.dumps(document)
        return write_tree(self, files) / "CATALOG.json"

    def _refuse(self, cases):
        built = [(self._catalog(edit(COMMITTED)), message) for edit, message in cases]
        assert_each_refused(self, ValueError, load_catalog, built)

    def test_header_drift_is_refused(self):
        self._refuse(
            (
                (setter("schema", "other"), f"schema is not {vocabulary.CATALOG_SCHEMA_ID}"),
                (setter("preserve_commit", "0" * 40), "preserve_commit drifted from vocabulary"),
                (setter("factory", "other"), "factory/generator drifted from vocabulary"),
                (setter("generator", "other"), "factory/generator drifted from vocabulary"),
                (setter("slice", "partial"), "slice drifted from vocabulary"),
                (setter("slice_mill", "lef-mill-r0"), "slice_mill drifted from vocabulary"),
                (
                    setter("slice_rows_file", "other.jsonl"),
                    "slice_rows_file drifted from vocabulary",
                ),
            )
        )

    def test_width_drift_is_refused(self):
        self._refuse(
            (
                (_move_rows, f"rows.jsonl short partition for {MILL_IDS[0]}"),
                (
                    setter("n_catalog_rows", COMMITTED["n_catalog_rows"] - 1),
                    "catalog n_catalog_rows drifted from mill widths",
                ),
                (
                    setter("plants_b", "n_pairs", vocabulary.PLANTS_B_PAIR_COUNT - 1),
                    "plants_b.jsonl n_pairs drifted from vocabulary",
                ),
            )
        )

    def test_archive_b_slug_pins_must_match_the_plant_rows(self):
        self._refuse(
            (
                (
                    setter("plants", "first_ok_slug", "x"),
                    "plants.jsonl first_ok_slug drifted from jsonl",
                ),
                (
                    setter("plants", "last_ok_slug", "x"),
                    "plants.jsonl last_ok_slug drifted from jsonl",
                ),
            )
        )

    def test_a_catalog_without_archive_b_loads_without_plants(self):
        document = {
            key: value for key, value in COMMITTED.items() if key not in {"plants", "plants_b"}
        }
        loaded = load_catalog(self._catalog(document))
        self.assertEqual((loaded.plants, loaded.plants_b), (None, None))

    def test_header_tables_are_superseded_by_the_slice_rows(self):
        header_tables = {name: [list(TABLE_ROWS[name])] for name in vocabulary.TABLE_NAMES}
        loaded = load_catalog(
            self._catalog(setter("mills", MILL_IDS[0], "tables", header_tables)(COMMITTED))
        )
        cache = loaded.mills[MILL_IDS[0]].tables["CACHE_OK"]
        self.assertEqual(
            (cache[0][0], len(cache)),
            (
                COMMITTED["mills"][MILL_IDS[0]]["first_slug"],
                COMMITTED["mills"][MILL_IDS[0]]["n_rows"],
            ),
        )

    def test_archive_b_plant_bytes_must_match_their_pin(self):
        rows = read_jsonl(PACKAGE / "plants.jsonl")
        rows[0]["extra"] = 1
        drifted = "".join(compact(row) + "\n" for row in rows)
        path = self._catalog(COMMITTED, {"plants.jsonl": drifted})
        with refusal(
            self, ValueError, "plants.jsonl sha256 drifted from CATALOG.json plants_sha256"
        ):
            load_catalog(path)


class TableExtractRefusals(unittest.TestCase):
    def test_table_source_refusals(self):
        extra_cache_row = f"CACHE_OK += [{TABLE_ROWS['CACHE_OK']!r}]\n"
        cases = (
            ("CACHE_OK = []\n", f"{MILL_PATH} missing catalog tables"),
            (TABLES_SOURCE + extra_cache_row, f"{MILL_PATH} catalog widths drifted"),
        )
        assert_each_refused(self, ValueError, _extract, cases)

    def test_unresolvable_list_extensions_are_ignored(self):
        ignored = "obj.attr = 1\nobj.attr += [1]\nUNKNOWN += [1]\nCACHE_OK += [call()]\n"
        record = _extract(TABLES_SOURCE + ignored)
        self.assertEqual((record["n_rows"], record["first_slug"]), (1, "cache_ok-0"))

    def test_table_summary_includes_the_tables(self):
        record = _extract(TABLES_SOURCE)
        summary = catalog_extract.mill_summary(record, include_tables=True)
        expected = {name: [list(TABLE_ROWS[name])] for name in vocabulary.TABLE_NAMES}
        self.assertEqual(summary["tables"], expected)

    def test_an_empty_slug_listing_is_refused(self):
        path = "experiments/.lef-used-slugs.txt"
        with refusal(self, ValueError, f"{path} used-slug listing is empty"):
            catalog_extract.extract_slugs_listing("", path=path)

    def test_dumps_rows_refuses_empty_and_ragged_tables(self):
        empty = {name: [] for name in vocabulary.TABLE_NAMES}
        ragged = {name: [TABLE_ROWS[name]] for name in vocabulary.TABLE_NAMES}
        ragged["SEED_OK"] = []
        cases = (
            (empty, "dumps_rows requires at least one catalog row"),
            (ragged, "dumps_rows table widths drifted"),
        )
        assert_each_refused(self, ValueError, catalog_extract.dumps_rows, cases)

    def test_plant_record_refuses_the_wrong_pair_count(self):
        path = "scripts/mill_plants.py"
        with refusal(self, ValueError, f"{path} expected 8 pairs, found 1"):
            plants_extract.extract_mill_plants_record(
                PLANT_APPEND,
                path=path,
                blob_sha="",
                archive_commit="",
                mill_id="m",
                catalog_first=1,
            )


class LefSharedSurface(SharedExtractSurfaceCases, unittest.TestCase):
    ast_module = catalog_ast
    extract_module = catalog_extract

    def test_annotated_assignment_returns_its_name_and_value(self):
        name, value = catalog_ast.assignment_of(ast.parse("X: int = 1").body[0])
        self.assertEqual((name, catalog_ast.literal_value(value)), ("X", 1))

    def test_dict_literals_resolve_only_when_every_entry_is_literal(self):
        self.assertEqual(self.literal("{'a': 1}"), {"a": 1})
        self.assertIs(self.literal("{'a': name}"), catalog_ast.UNSET)


if __name__ == "__main__":
    unittest.main()
