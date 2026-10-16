"""IAC fail-closed branches reached through the public surface only.

``catalog.load_catalog`` on mutated temp copies of ``pipelines/iac/CATALOG.json``
and its plants sidecars, and the ``catalog_extract`` / ``catalog_ast``
extractors on small in-memory sources.
"""

from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
support = importlib.import_module("mill_public_branch_support")
catalog = importlib.import_module("iac.catalog")
catalog_ast = importlib.import_module("iac.catalog_ast")
extract = importlib.import_module("iac.catalog_extract")

PACKAGE = support.REPO / "pipelines" / "iac"
PATH = "experiments/iac-mill-r609.py"
NOTHING = f"{PATH} has no extractable IAC catalog assignment"
DROP_TEST = "if pair[0]['slug'] not in _DROP_SUCCESS"
DROP_FILTER = f"[pair for pair in PAIRS {DROP_TEST}]"
R609 = (
    "PAIRS = [({'slug': 'keep-a', 'plant': 'p'}, {'slug': 'keep-a-fail', 'handoff': True}),"
    " ({'slug': 'drop-me'}, {'slug': 'drop-fail'})]\n"
    "_DROP_SUCCESS = {'drop-me'}\n"
    f"PAIRS = {DROP_FILTER}\n"
    "_EXTRA = [({'slug': 'extra-a'}, {'slug': 'extra-fail'})]\n"
    "OTHER.extend(_EXTRA)\n"
    "PAIRS.extend(_EXTRA)\n"
)


def extracted(source: str) -> dict:
    return extract.extract_mill_catalog(source, path=PATH)


def extract_error(source: str) -> str | None:
    return support.error_text(ValueError, extracted, source)


class IacLiteralAst(support.LiteralAstContract, unittest.TestCase):
    ast_module = catalog_ast

    def test_call_kwargs_need_a_keyword_only_name_call(self):
        for expression in ("x", "obj.f(a=1)", "f(1, a=1)", "f(**kw)", "f(a=x)"):
            with self.subTest(expression):
                self.assertIsNone(catalog_ast.call_kwargs(support.parsed(expression)))


class IacExtractNaming(support.ExtractNamingContract, unittest.TestCase):
    extract = extract

    def test_companion_path_is_none_without_mill_or_out(self):
        sources = ("OUT = ROOT / 'g.py'\n", "X = 1\n")
        found = [extract.extract_companion_path(source) for source in sources]
        self.assertEqual(found, ["g.py", None])


class IacCatalogPins(support.SourceBoundCatalogContract, unittest.TestCase):
    catalog = catalog
    catalog_dir = PACKAGE
    sidecars = ("plants.jsonl", "plants_b.jsonl")
    slice_mill = "iac-mill-r609"
    slice_label = "r609"

    def test_blank_plants_lines_are_skipped(self):
        copy = self.copy()
        lines = copy.path("plants.jsonl").read_bytes().splitlines(keepends=True)
        document = copy.read_json()
        document["plants_sha256"] = copy.write_bytes(b"".join([lines[0], b"  \n", *lines[1:]]))
        loaded = catalog.load_catalog(copy.write_json(document))
        self.assertEqual(loaded.plants, catalog.CATALOG.plants)


class IacR609Rebuild(unittest.TestCase):
    def test_the_drop_filter_and_extends_rebuild_the_slice(self):
        record = extracted(R609)
        found = (record["shape"], record["n_rows"], record["first_slug"], record["last_slug"])
        self.assertEqual(found, (extract.SHAPE_LITERAL, 2, "keep-a", "extra-a"))

    def test_any_other_drop_filter_extracts_nothing(self):
        for label, comprehension in (
            ("two generators", f"[pair for pair in PAIRS for x in Y {DROP_TEST}]"),
            ("element is not a name", f"[pair[0] for pair in PAIRS {DROP_TEST}]"),
            ("element is not the target", f"[x for pair in PAIRS {DROP_TEST}]"),
            ("iterable is a call", f"[pair for pair in f(PAIRS) {DROP_TEST}]"),
        ):
            with self.subTest(label):
                source = R609.replace(DROP_FILTER, comprehension)
                self.assertEqual(extract_error(source), NOTHING)

    def test_pairs_that_are_not_two_objects_extract_nothing(self):
        for label, row in (("text row", "'junk'"), ("text pair", "('a', 'b')")):
            with self.subTest(label):
                source = R609.replace("PAIRS = [(", f"PAIRS = [{row}, (", 1)
                self.assertEqual(extract_error(source), NOTHING)


class IacTableShapes(unittest.TestCase):
    def test_suc_fail_lists_need_a_first_success_slug(self):
        for label, source in (
            ("mixed items", "PAIRS = [(_suc(slug='a'), _fail(slug='b')), 3]\n"),
            ("no first slug", "PAIRS = [(_suc(), _fail(slug='b'))]\n"),
        ):
            with self.subTest(label):
                self.assertEqual(extract_error(source), NOTHING)

    def test_cli_spec_must_be_a_list(self):
        source = "K8S = [('a-vs-old', 'g')]\nCLI_SPEC = 'x'\n"
        self.assertEqual(extract_error(source), NOTHING)

    def test_short_k8s_rows_and_non_object_cli_rows_extract_nothing(self):
        source = "K8S = [('only',)]\nCLI_SPEC = ['x']\n"
        self.assertEqual(extract_error(source), NOTHING)


if __name__ == "__main__":
    unittest.main()
