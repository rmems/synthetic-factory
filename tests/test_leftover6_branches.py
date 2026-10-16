"""Fail-closed branches of the leftover6 catalog loader and literal extractor.

The loader cases copy the committed catalog into a temporary directory, apply one
edit, and pin the exact ``CatalogError`` the loader raises today. Edits land before
the row-content pins on purpose: each one proves that an earlier, more specific
guard decides the refusal. The header-count disagreements in
``_validate_source_counts`` are not driven because every mill descriptor, including
its ``n_rows``, is pinned by digest before that guard runs.
"""

import ast
import json
import tempfile
import unittest
from pathlib import Path

from pipelines.leftover6 import (
    CATALOG,
    CatalogError,
    is_vendor_filename,
    load_catalog,
    refuse_vendor_paths,
)
from pipelines.leftover6.catalog_extract import (
    SSL_PAIR_FIELDS,
    SSL_PATH,
    UNSET,
    extract_source,
    literal_value,
)
from pipelines.leftover6.catalog_literals import _row_definition

CONFIG_DIR = Path(__file__).resolve().parents[1] / "config" / "leftover6"
HEADER = "CATALOG.json"
PAIRS = "pairs.jsonl"
PLANTS = "plants.jsonl"
FIRST_SSL_LINE = 17
RENAMED = "renamed-identity"
SSL_ROW = {field: 1 if field == "novel" else f"{field}-value" for field in SSL_PAIR_FIELDS}
SSL_SOURCE = (
    "FACTORY = 'stateful-service-lineage-factory'\nGEN = 'grok-4.6'\n"
    f"START = 164\nN_ROUNDS = 1\nPAIRS = [{SSL_ROW!r}]\n"
)


def _committed(name):
    return (CONFIG_DIR / name).read_bytes()


def _rows(name):
    return [json.loads(line) for line in _committed(name).decode("utf-8").splitlines()]


def _jsonl(rows):
    return "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in rows).encode()


def _row_edit(name, line, field, value):
    rows = _rows(name)
    rows[line - 1][field] = value
    return {name: _jsonl(rows)}


def _replace_line(name, line, text):
    lines = _committed(name).decode("utf-8").splitlines()
    lines[line - 1] = text
    return {name: ("\n".join(lines) + "\n").encode()}


def _header_edit(key, value):
    header = json.loads(_committed(HEADER))
    header[key] = value(header[key]) if callable(value) else value
    return {HEADER: json.dumps(header).encode()}


# (label, {filename: replacement bytes}, exact CatalogError message)
LOADER_CASES = (
    ("header is not an object", {HEADER: b"[]"}, "catalog must be an object"),
    ("three mills", _header_edit("catalogs", lambda mills: mills[:2]),
     "catalog.catalogs must list the three leftover6 mills"),
    ("empty pairs", {PAIRS: b""}, "pairs.jsonl must contain at least one row"),
    ("indented pair", _replace_line(PAIRS, 1, " " + json.dumps(_rows(PAIRS)[0])),
     "pairs.jsonl:1 is not compact"),
    ("pair is a list", _replace_line(PAIRS, 1, "[]"),
     "pairs.jsonl:1 must be a leftover6 pair object"),
    ("pair without kind", _replace_line(PAIRS, 1, '{"slug":"x"}'),
     "pairs.jsonl:1 must be a leftover6 pair object"),
    ("unknown pair kind", _row_edit(PAIRS, 1, "kind", "rpc-pairs"),
     "pairs.jsonl:1 kind is not a leftover6 pair"),
    ("blank pair text", _row_edit(PAIRS, 1, "fail", " "),
     "pairs.jsonl:1.fail must be a non-empty string"),
    ("ssl novel floor", _row_edit(PAIRS, FIRST_SSL_LINE, "novel", 0),
     f"pairs.jsonl:{FIRST_SSL_LINE}.novel out of range: 0"),
    ("plant increment floor", _row_edit(PLANTS, 1, "inc", 0), "plants.jsonl:1.inc out of range: 0"),
    ("blank schema version", _header_edit("schema_version", " "),
     "catalog.schema_version must be a non-empty string"),
    ("gql endpoint", _row_edit(PAIRS, 1, "slug", RENAMED),
     "gql leftover6 slugs drifted from header"),
    ("ssl endpoint", _row_edit(PAIRS, FIRST_SSL_LINE, "slug", RENAMED),
     "ssl leftover6 slugs drifted from header"),
    ("sbox endpoint", _row_edit(PLANTS, 1, "family", RENAMED),
     "sbox leftover6 slugs drifted from header"),
    ("gql row source", _row_edit(PAIRS, 2, "source_path", "experiments/other.py"),
     "gql leftover6 pair source_path drifted"),
    ("ssl row source", _row_edit(PAIRS, FIRST_SSL_LINE + 1, "source_path", "experiments/other.py"),
     "ssl leftover6 pair source_path drifted"),
    ("sbox row source", _row_edit(PLANTS, 2, "source_path", "experiments/other.py"),
     "sbox leftover6 pair source_path drifted"),
)

# (label, expression, environment) where every expression must stay UNSET
UNPROVEN_LITERALS = (
    ("mapping unpacking", "{**base}", {}),
    ("unbound mapping value", "{'key': unbound}", {}),
    ("repeated mapping key", "{'key': 1, 'key': 2}", {}),
    ("positional dict()", "dict(1)", {}),
    ("unbound dict() keyword", "dict(key=unbound)", {}),
    ("keyword _row()", "_row(family='fixture')", {"_row": _row_definition()}),
)


def _write_tree(dest, replacements):
    for name in (HEADER, PAIRS, PLANTS):
        (dest / name).write_bytes(replacements.get(name, _committed(name)))


class Leftover6LoaderRefusals(unittest.TestCase):
    def test_each_edit_raises_its_exact_refusal(self):
        for label, replacements, message in LOADER_CASES:
            with self.subTest(label), tempfile.TemporaryDirectory() as temp:
                dest = Path(temp)
                _write_tree(dest, replacements)
                with self.assertRaises(CatalogError) as caught:
                    load_catalog(dest)
                self.assertEqual(str(caught.exception), message)

    def test_header_that_is_not_json_names_the_header_path(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp)
            _write_tree(dest, {HEADER: b"{"})
            with self.assertRaises(CatalogError) as caught:
                load_catalog(dest)
        self.assertTrue(
            str(caught.exception).startswith(f"cannot load leftover6 catalog {dest / HEADER}: ")
        )

    def test_committed_catalog_exposes_mills_and_row_counts(self):
        mills = list(CATALOG.mills())
        self.assertEqual([mill.kind for mill in mills], ["gql-pairs", "ssl-pairs", "sbox-plants"])
        self.assertEqual((CATALOG.n_pair_rows, CATALOG.n_plant_rows), (32, 65))


class Leftover6VendorNames(unittest.TestCase):
    def test_vendor_filename_needs_python_leftover6_and_a_mill_token(self):
        cases = (
            ("leftover6_mill.txt", False),
            ("notes.py", False),
            ("leftover6_notes.py", False),
            ("gql_leftover6_loop.py", True),
            ("_gen_leftover6.py", True),
        )
        for name, expected in cases:
            with self.subTest(name):
                self.assertIs(is_vendor_filename(name), expected)

    def test_non_vendor_paths_pass_the_refusal(self):
        self.assertIsNone(refuse_vendor_paths(["notes.py", Path("leftover6/README.md")]))


class Leftover6LiteralExtraction(unittest.TestCase):
    def test_unproven_literals_stay_unset(self):
        for label, expression, env in UNPROVEN_LITERALS:
            with self.subTest(label):
                node = ast.parse(expression, mode="eval").body
                self.assertIs(literal_value(node, env), UNSET)

    def test_inert_statements_and_bare_annotations_do_not_block_extraction(self):
        source = "pass\nNOTE: str\n" + SSL_SOURCE
        found = extract_source(source, path=SSL_PATH)
        self.assertEqual((found["n_rows"], found["first_slug"]), (1, "slug-value"))

    def test_extracted_integers_respect_the_exact_decimal_limit(self):
        source = SSL_SOURCE.replace("START = 164", "START = " + "1" * 4097)
        with self.assertRaises(ValueError) as caught:
            extract_source(source, path=SSL_PATH)
        self.assertEqual(
            str(caught.exception), f"{SSL_PATH} START exceeds the exact-decimal integer limit"
        )

    def test_literal_rows_must_carry_every_reviewed_field(self):
        source = SSL_SOURCE.replace(repr(SSL_ROW), "{'slug': 'only'}")
        with self.assertRaises(ValueError) as caught:
            extract_source(source, path=SSL_PATH)
        self.assertEqual(
            str(caught.exception), f"{SSL_PATH} PAIRS[0] keys drifted from {SSL_PAIR_FIELDS}"
        )


if __name__ == "__main__":
    unittest.main()
