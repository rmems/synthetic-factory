"""LEF catalog load, pin binding, and AST extract: one test per refusal or fall-through branch."""

from __future__ import annotations

import ast
import json
import sys
import tempfile
import unittest
from collections.abc import Iterable
from dataclasses import replace
from pathlib import Path
from typing import Any
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))
sys.path.insert(0, str(REPO / "tests"))

from lef import catalog as lef_catalog
from lef import catalog_ast as lef_ast
from lef import catalog_extract as lef_extract
from lef import vocabulary as lv
from lef.catalog import CATALOG
from lef.catalog_extract import extract_mill_catalog, jsonable, mill_summary, rebuild_stem_tables
from lef.plants_extract import extract_plant_pairs
from lef.sources import catalog_sources, plant_sources
from test_lef import _STEMS_SNIPPET, _TABLES_SNIPPET


def _first_rows(name: str, count: int) -> list[str]:
    package = REPO / "pipelines" / "lef"
    return (package / name).read_text(encoding="utf-8").splitlines()[:count]


def _first(items: Iterable[Any], what: str) -> Any:
    """The first item, or an AssertionError naming what was expected."""

    try:
        return next(iter(items))
    except StopIteration:
        raise AssertionError(f"expected at least one {what}") from None


class LefRefusalBranchTests(unittest.TestCase):
    """Each load, bind, and extract refusal fires with its own message."""

    def _jsonl(self, text: str) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "rows.jsonl"
        path.write_text(text, encoding="utf-8", newline="")
        return path

    def test_slice_rows_refuse_each_framing_and_row_defect(self):
        first, second = _first_rows("rows.jsonl", 2)
        row = json.loads(first)
        short = dict(row, CACHE_OK=row["CACHE_OK"][:2])
        cases = (
            (f"{first}\n\n{second}\n", "rows.jsonl:2 is empty"),
            (f"{first}\n{{nope\n", "rows.jsonl:2 is not JSON"),
            (f"{second}\n", "rows.jsonl:1 index drifted from 0"),
            ("[]\n", "rows.jsonl:1 index drifted from 0"),
            (json.dumps(short) + "\n", "rows.jsonl:1 CACHE_OK arity drifted"),
            ("", "must be LF-framed jsonl"),
        )
        for text, message in cases:
            path = self._jsonl(text)
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                lef_catalog._parse_slice_rows(path)
        with self.assertRaisesRegex(ValueError, "cannot load leftover slice"):
            lef_catalog._parse_slice_rows(REPO / "missing" / "rows.jsonl")

    def test_plant_rows_refuse_each_row_defect(self):
        (first,) = _first_rows("plants.jsonl", 1)
        row = json.loads(first)
        cases = (
            ("\n", "plants.jsonl:1 is empty"),
            (f" {first}\n", "plants.jsonl:1 must be compact jsonl"),
            ("{nope\n", "plants.jsonl:1 is not JSON"),
            ("[]\n", "plants.jsonl:1 is not an object"),
            (json.dumps(dict(row, i=3)) + "\n", "plants.jsonl:1 index drifted from 0"),
            (json.dumps(dict(row, bad=None)) + "\n", "plants.jsonl:1 missing ok/bad objects"),
            (f"{first}\n", r"plants.jsonl row count 1 != 2"),
        )
        for text, message in cases:
            path = self._jsonl(text).with_name("plants.jsonl")
            path.write_text(text, encoding="utf-8")
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                lef_catalog._parse_plants_jsonl(path, expected=2)

    def test_slug_pin_refusals(self):
        drifted = replace(CATALOG.slugs, blob_sha="0" * 40)
        with self.assertRaisesRegex(ValueError, "disagrees with sources.py"):
            lef_catalog._bind_slug_pin(drifted)
        with (
            mock.patch.object(lef_catalog, "slug_sources", return_value=()),
            self.assertRaisesRegex(ValueError, "expected one leftover used-slug"),
        ):
            lef_catalog._bind_slug_pin(CATALOG.slugs)

    def test_mill_pin_shape_and_table_refusals(self):
        tables_mill = CATALOG.mills["lef-mill-r629"]
        stems_mill = CATALOG.mills["lef-mill-r968"]
        source = _first(
            (s for s in catalog_sources() if s.mill_id == "lef-mill-r629"), "r629 source pin"
        )
        cases = (
            (replace(tables_mill, path="x.py"), "pin disagrees"),
            (replace(tables_mill, kind=lv.KIND_STEMS), "kind disagrees"),
            (replace(tables_mill, n_table_rows=1), "n_table_rows does not match"),
            (replace(tables_mill, n_pair_slots=1), "n_pair_slots does not match"),
        )
        for mill, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                lef_catalog._bind_mill("lef-mill-r629", mill, source)
        shapes = (
            (replace(tables_mill, kind=lv.KIND_STEMS), "tables shape must use kind=tables"),
            (replace(tables_mill, shape="loose"), "unknown shape 'loose'"),
            (replace(stems_mill, kind=lv.KIND_TABLES), "stems shape must use kind=stems"),
            (replace(stems_mill, stems=(("a", "b", "c"),)), "must omit stems"),
        )
        for mill, message in shapes:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                lef_catalog._bind_mill_shape("m", mill)
        tables = dict(tables_mill.tables)
        first_row = (("other",) + tables["CACHE_OK"][0][1:],) + tables["CACHE_OK"][1:]
        last_row = tables["CACHE_OK"][:-1] + (("other",) + tables["CACHE_OK"][-1][1:],)
        table_cases = (
            (replace(tables_mill, tables=None), "omitted tables"),
            (replace(tables_mill, tables=dict(tables, SEED_OK=())), "SEED_OK width drifted"),
            (replace(tables_mill, tables=dict(tables, CACHE_OK=first_row)), "first_slug drifted"),
            (replace(tables_mill, tables=dict(tables, CACHE_OK=last_row)), "last_slug drifted"),
        )
        for mill, message in table_cases:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                lef_catalog._bind_mill_tables("m", mill)

    def test_archive_b_plant_pin_refusals(self):
        plants = CATALOG.plants
        if plants is None:
            self.fail("the committed catalog has no Archive B plants")
        pins = {pin.mill_id: pin for pin in plant_sources()}
        slot = lef_catalog._PlantSlot("plants_b", "plants_b.jsonl", lv.PLANTS_PAIR_COUNT)
        cases = (
            (replace(plants, mill_id="unknown"), "Archive B plants_b mill_id missing"),
            (replace(plants, path="x.py"), "Archive B plants_b pin disagrees"),
            (replace(plants, blob_sha="0" * 40), "Archive B plants_b blob_sha disagrees"),
            (replace(plants, kind=lv.KIND_TABLES), "Archive B plants_b kind disagrees"),
            (replace(plants, n_pairs=7), "Archive B plants_b n_pairs drifted"),
            (replace(plants, pairs=plants.pairs[:1]), "plants_b.jsonl width drifted"),
        )
        for value, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                lef_catalog._bind_plants(value, pins, slot)

    def test_literal_value_resolves_each_node_kind(self):
        env = {"BASE": ["a"]}
        cases = (
            ("-3", -3),
            ("-'a'", lef_ast.UNSET),
            ("not 1", lef_ast.UNSET),
            ("'a' + 'b'", "ab"),
            ("'a' + 1", lef_ast.UNSET),
            ("1 - 2", lef_ast.UNSET),
            ("frozenset(['x', 'y'])", frozenset({"x", "y"})),
            ("frozenset(1)", lef_ast.UNSET),
            ("pkg.frozenset(['x'])", lef_ast.UNSET),
            ("BASE", ["a"]),
            ("MISSING", lef_ast.UNSET),
            ("{1, 2}", {1, 2}),
            ("lambda: 1", lef_ast.UNSET),
        )
        for text, expected in cases:
            with self.subTest(text=text):
                value = lef_ast.literal_value(ast.parse(text, mode="eval").body, env)
                if expected is lef_ast.UNSET:
                    self.assertIs(value, lef_ast.UNSET)
                else:
                    self.assertEqual(value, expected)

    def test_round_linear_mod_rejects_each_non_formula_shape(self):
        rejected = (
            "floor(0.5 + (i % 3) * 0.1, 2)",
            "round(0.5 + (i % 3) * 0.1)",
            "round(0.5 + (i % 3) * 0.1, 'x')",
            "round(0.5 - (i % 3) * 0.1, 2)",
            "round(1 + (i % 3) * 0.1, 2)",
            "round(0.5 + (i % 3) / 0.1, 2)",
            "round(0.5 + (i % 3) * 1, 2)",
            "round(0.5 + (i + 3) * 0.1, 2)",
            "round(0.5 + (j % 3) * 0.1, 2)",
            "round(0.5 + (i % 'x') * 0.1, 2)",
        )
        for text in rejected:
            with self.subTest(text=text):
                self.assertIsNone(lef_extract._round_linear_mod(ast.parse(text, mode="eval").body))
        accepted = lef_extract._round_linear_mod(
            ast.parse("round(0.5 + (i % 3) * 0.1, 2)", mode="eval").body
        )
        self.assertEqual(accepted, {"base": 0.5, "mod": 3, "step": 0.1, "ndigits": 2})

    def test_stem_rebuild_refuses_malformed_stems_and_lims(self):
        formula = lv.NUMS_FORMULA
        cases = (
            ([("a", "b")], [("1", "2")], "STEMS\\[0\\] is not a 3-tuple"),
            ([(1, "b", "c")], [("1", "2")], "STEMS\\[0\\] name is not a string"),
            ([("a", "b", "c"), ("d", "e", "f")], [("1", "2"), ("3",)], "LIMS\\[1\\] is not"),
        )
        for stems, lims, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                rebuild_stem_tables(stems, ["f"], ["c"], lims, formula)

    def test_extract_falls_back_and_refuses_table_arity(self):
        unpinned = _TABLES_SNIPPET.replace("CATALOG_FIRST = 629\n", "GEN = make_gen()\n")
        extracted = extract_mill_catalog(unpinned, path="experiments/lef-mill-r77.py")
        self.assertEqual(extracted["catalog_first"], 77)
        self.assertEqual(extracted["generator"], lv.GENERATOR)
        first_row = (
            '("azure-api-version-unkeyed", "azure_api_version", 0.93, 0.21, 0.9,\n'
            '     "2024-02-01", "2024-06-01", "avoided-a", "ticket-a")'
        )
        self.assertIn(first_row, _TABLES_SNIPPET)
        for row, message in (('("short", "row")', "CACHE_OK\\[0\\] arity 2 != 9"),
                             ('"loose"', "CACHE_OK\\[0\\] arity str != 9")):
            broken = _TABLES_SNIPPET.replace(first_row, row)
            with self.subTest(row=row), self.assertRaisesRegex(ValueError, message):
                extract_mill_catalog(broken, path="experiments/lef-mill-r629.py")

    def test_stem_summary_includes_pools_only_with_tables(self):
        record = extract_mill_catalog(_STEMS_SNIPPET, path="experiments/lef-mill-r968.py")
        full = mill_summary(record, include_tables=True)
        self.assertEqual(full["stems"], [list(row) for row in record["stems"]])
        self.assertEqual(full["lims"], [list(row) for row in record["lims"]])
        self.assertEqual(full["nums"], lv.NUMS_FORMULA)
        bare = mill_summary(dict(record, nums=None), include_tables=False)
        self.assertNotIn("stems", bare)
        self.assertNotIn("nums", bare)
        self.assertEqual(
            jsonable({"t": (1, [2]), "s": {"b", "a"}, "f": frozenset({3})}),
            {"t": [1, [2]], "s": ["a", "b"], "f": [3]},
        )

    def test_plant_pairs_refuse_each_append_defect(self):
        ok, bad = '_ok(slug="a")', '_bad(slug="b")'
        skipped = (
            f'"doc"\nfoo()\nPAIRS.extend(({ok}, {bad}))\nself.PAIRS.append(1)\n'
            "PAIRS.append(1, 2)\nMORE.append(1)\n"
        )
        self.assertEqual(
            len(extract_plant_pairs(skipped + f"PAIRS.append(({ok}, {bad}))\n", path="p.py")), 1
        )
        cases = (
            ("PAIRS.append(1)", "p.py PAIRS.append is not an \\(_ok, _bad\\) tuple"),
            (f"PAIRS.append(({ok}, other()))", "side is not _ok/_bad"),
            (f"PAIRS.append(({ok}, _bad(slug=name)))", "side is not _ok/_bad"),
            (f"PAIRS.append(({ok}, _bad(**sides)))", "side is not _ok/_bad"),
            (f"PAIRS.append(({bad}, {ok}))", "order must be _ok then _bad"),
            (f"PAIRS.append((_ok(x=1), {bad}))", "missing slug"),
            ("x = 1", "p.py has no PAIRS.append plant pairs"),
        )
        for text, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                extract_plant_pairs(text + "\n", path="p.py")


if __name__ == "__main__":
    unittest.main()
