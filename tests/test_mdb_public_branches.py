"""MDB fail-closed branches reached through the public surface only.

``catalog.load_catalog`` and ``pairs.load_pairs`` on mutated temp copies of
``pipelines/mdb/CATALOG.json`` / ``pairs.jsonl``, and the ``catalog_extract`` /
``catalog_ast`` extractors on small in-memory sources.
"""

from __future__ import annotations

import importlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
support = importlib.import_module("mill_public_branch_support")
catalog = importlib.import_module("mdb.catalog")
catalog_ast = importlib.import_module("mdb.catalog_ast")
extract = importlib.import_module("mdb.catalog_extract")
pairs = importlib.import_module("mdb.pairs")

PACKAGE = support.REPO / "pipelines" / "mdb"
PATH = "experiments/mdb-mill-r12.py"
NOTHING = f"{PATH} has no extractable MDB catalog assignment"
LINES = (PACKAGE / "pairs.jsonl").read_bytes().splitlines(keepends=True)
ROWS = [json.loads(line) for line in LINES]
NO_SLUG_PAIRS = (
    "X = 1\n",
    "PAIRS = [('a', 'b')]\n",
    "PAIRS = [({'slug': 1}, {'slug': 'b'})]\n",
    "PAIRS = [(P('a', 'x'), P('b', 'y')), 3]\n",
    "PAIRS = [(P(a, 'x'), P('b', 'y'))]\n",
    "PAIRS = [(P(1, 'x'), P('b', 'y'))]\n",
    "SLUGS = 'ab'\n",
    "SLUGS = ['a', 1]\n",
    "SLUGS = ['a', 'b', 'c']\n",
    "RAW = 'x'\n",
    "TOOLS = 'x'\n",
)


def compact(row: dict) -> bytes:
    return (pairs.dumps_pair_line(row) + "\n").encode("utf-8")


def mill_indexes(mill_id: str) -> list[int]:
    return [index for index, row in enumerate(ROWS) if row[support.MILL_ID] == mill_id]


class MdbLiteralAst(support.LiteralAstContract, unittest.TestCase):
    ast_module = catalog_ast

    def test_call_posargs_need_a_name_call_of_literals(self):
        for expression in ("x", "obj.f(1)", "f(1, x)"):
            with self.subTest(expression):
                self.assertIsNone(catalog_ast.call_posargs(support.parsed(expression)))

    def test_with_name_paths_need_one_python_file_name(self):
        for expression, expected in (
            ("Path(__file__).with_name('m.py')", "experiments/m.py"),
            ("f('m.py')", None),
            ("p.with_suffix('m.py')", None),
            ("p.with_name('m.py', 'x')", None),
            ("p.with_name('m.txt')", None),
        ):
            with self.subTest(expression):
                found = catalog_ast.with_name_path(support.parsed(expression))
                self.assertEqual(found, expected)

    def test_source_paths_skip_names_that_resolve_to_nothing(self):
        sources = ("MILL = 1\nOUT = Path(__file__).with_name('m.py')\n", "X = 1\n")
        found = [extract.extract_companion_path(source) for source in sources]
        self.assertEqual(found, ["experiments/m.py", None])


class MdbExtractNaming(support.ExtractNamingContract, unittest.TestCase):
    extract = extract


class MdbCatalogPins(support.SourceBoundCatalogContract, unittest.TestCase):
    catalog = catalog
    catalog_dir = PACKAGE
    slice_mill = "mdb-mill-r709"
    slice_label = "r709"

    def test_document_pins_must_match_the_vocabulary(self):
        schema = self.copy().read_json()["schema"]
        for key, message in (
            ("schema", f"schema is not {schema}"),
            ("preserve_commit", "preserve_commit drifted from vocabulary"),
            ("factory", "factory/generator drifted from vocabulary"),
            ("generator", "factory/generator drifted from vocabulary"),
            ("slice", "slice drifted from vocabulary"),
        ):
            with self.subTest(key):
                copy = self.copy()
                written = copy.write_json(support.mutated(copy.read_json(), (key,), "drifted"))
                found = support.error_text(ValueError, catalog.load_catalog, written)
                self.assertEqual(found, f"{written} {message}")


class MdbExtractShapes(unittest.TestCase):
    def test_a_non_int_catalog_first_falls_back_to_the_file_name(self):
        source = "CATALOG_FIRST = 'x'\nSLUGS = ['a', 'b']\n"
        record = extract.extract_mill_catalog(source, path=PATH)
        self.assertEqual((record["catalog_first"], record["shape"]), (12, extract.SHAPE_SLUGS))

    def test_tables_that_are_not_literal_slug_pairs_extract_nothing(self):
        for source in NO_SLUG_PAIRS:
            with self.subTest(source):
                found = support.error_text(
                    ValueError, extract.extract_mill_catalog, source, path=PATH
                )
                self.assertEqual(found, NOTHING)


class MdbPairsFile(unittest.TestCase):
    def load_error(self, payload: bytes) -> str | None:
        path = support.temp_dir(self) / "pairs.jsonl"
        path.write_bytes(payload)
        return support.error_text(ValueError, pairs.load_pairs, path)

    def test_framing_and_line_shape_refusals(self):
        spaced = json.dumps(ROWS[0], sort_keys=True).encode() + b"\n"
        for label, payload, message in (
            ("row dropped", b"".join(LINES[:-1]),
             f"pairs.jsonl has {len(LINES) - 1} rows, expected {len(LINES)}"),
            ("no final newline", b"".join(LINES).rstrip(b"\n"),
             "pairs.jsonl must end with a newline"),
            ("indented", b" " + LINES[0], "pairs.jsonl:1 is empty or indented"),
            ("not json", b"nope\n",
             "pairs.jsonl:1 is not JSON: Expecting value: line 1 column 1 (char 0)"),
            ("keys", b'{"a":1}\n', f"pairs.jsonl:1 keys drifted from {pairs.PAIR_KEYS}"),
            ("spaced", spaced, "pairs.jsonl:1 is not compact sorted JSON"),
        ):
            with self.subTest(label):
                self.assertEqual(self.load_error(payload), message)

    def test_rows_must_bind_to_the_catalog_mills(self):
        first, mill = ROWS[0], ROWS[0][support.MILL_ID]
        key = (mill, first["success_slug"], first["fail_slug"])
        for label, line, message in (
            ("unknown mill", compact(first | {support.MILL_ID: "mdb-mill-r0"}),
             "pairs.jsonl mills drifted: extra=['mdb-mill-r0'] missing=[]"),
            ("path", compact({**first, "path": "experiments/x.py"}),
             f"{mill} path disagrees with catalog pins"),
            ("duplicate", LINES[0], f"duplicate deferred pair {key}"),
        ):
            with self.subTest(label):
                payload = b"".join([LINES[0], line, *LINES[2:]])
                self.assertEqual(self.load_error(payload), message)

    def test_each_mill_keeps_its_count_and_boundary_slugs(self):
        mill = ROWS[0][support.MILL_ID]
        indexes = mill_indexes(mill)
        before_last, last = indexes[-2:]
        target = pairs.deferred_sources()[-1]
        moved = compact(ROWS[0] | {support.MILL_ID: target.mill_id, "path": target.path})
        count = f"{mill} has {len(indexes) - 1} jsonl rows, catalog n_rows={len(indexes)}"
        for label, swap, message in (
            ("count", {0: moved}, count),
            ("first slug", {0: LINES[1], 1: LINES[0]}, f"{mill} first_slug drifted from catalog"),
            ("last slug", {last: LINES[before_last], before_last: LINES[last]},
             f"{mill} last_slug drifted from catalog"),
        ):
            with self.subTest(label):
                lines = [swap.get(index, line) for index, line in enumerate(LINES)]
                self.assertEqual(self.load_error(b"".join(lines)), message)


if __name__ == "__main__":
    unittest.main()
