"""Fail-closed branches of the sir catalog loader, extractor, and identity helpers.

Loader cases copy the committed ``CATALOG.json`` / ``pairs.jsonl`` into a temporary
directory and pin the exact ``ValueError`` raised today. Two loader guards are not
driven: the source-inventory mismatch and the two-mill count both sit behind the
pair-file SHA-256 pin, which any mill rename breaks first.
"""

import ast
import json
import tempfile
import unittest
from pathlib import Path

from pipelines.sir import load_catalog, refuse_vendor_paths, source_by_id
from pipelines.sir.catalog_extract import (
    _literal_sibling_path,
    catalog_document,
    dumps_catalog,
    dumps_pairs,
    extract_mill_catalog,
    mill_kind_for_id,
    write_catalog_files,
)
from pipelines.sir.catalog_literals import UNSET, literal_value, module_docstring
from pipelines.sir.identity import forbidden_globs, is_vendor_filename
from pipelines.sir.vocabulary import FORBIDDEN_MILL_GLOBS
from tests.test_sir import _LEFTOVER_SNIPPET

PACKAGE_DIR = Path(__file__).resolve().parents[1] / "pipelines" / "sir"
CATALOG_NAME = "CATALOG.json"
PAIRS_NAME = "pairs.jsonl"
R72 = "sir-mill-leftover3-r72"
R72_PATH = "experiments/sir-mill-leftover3-r72.py"
R108_PATH = "experiments/sir_r108_leftover3d_mill.py"
HEADER_LINES = (
    'FACTORY = "search-index-rebuild-factory"\nGEN = "grok-4.6"\nCATALOG_FIRST = 72\n'
)


def _committed(name):
    return (PACKAGE_DIR / name).read_bytes()


def _pair_line_edit(transform):
    lines = _committed(PAIRS_NAME).decode("utf-8").split("\n")
    lines[0] = transform(lines[0])
    return {PAIRS_NAME: "\n".join(lines).encode()}


def _drop_first_key(line):
    row = json.loads(line)
    row.pop("fail_url")
    return json.dumps(row, separators=(",", ":"))


def _header_edit(edit):
    document = json.loads(_committed(CATALOG_NAME))
    edit(document)
    return {CATALOG_NAME: json.dumps(document).encode()}


def _set_count(document):
    document["n_mills"] = "2"


def _set_slug(field):
    def edit(document):
        document["mills"][R72][field] = "drifted-slug"

    return edit


def _pairs_source(pairs):
    return HEADER_LINES + f"PAIRS = {pairs!r}\n"


SIX = ("slug", "engine", "wrong", "fix", "ticket", "https://example.com/doc")

# (label, {filename: replacement bytes}, exact ValueError message)
LOADER_CASES = (
    ("indented pair line", _pair_line_edit(lambda line: " " + line),
     "pairs.jsonl:1 is not a compact JSONL record"),
    ("pair keys drift", _pair_line_edit(_drop_first_key),
     "pairs.jsonl:1 keys drifted from PAIR_FIELD_ORDER"),
    ("count type", _header_edit(_set_count), "catalog n_mills must be an integer"),
    ("first slug", _header_edit(_set_slug("first_slug")),
     f"{R72} first_slug disagrees with jsonl"),
    ("last slug", _header_edit(_set_slug("last_slug")), f"{R72} last_slug disagrees with jsonl"),
)

# (label, source, path, exact ValueError message)
EXTRACT_CASES = (
    ("foreign directory", _LEFTOVER_SNIPPET, "other/sir_r108_leftover3d_mill.py",
     f"other/sir_r108_leftover3d_mill.py does not match owned sir mill source path {R108_PATH!r}"),
    ("empty factory", _LEFTOVER_SNIPPET.replace('"search-index-rebuild-factory"', '""'), R72_PATH,
     f"{R72_PATH} FACTORY is not a non-empty string"),
    ("round count", _LEFTOVER_SNIPPET + "N_ROUNDS = 2\n", R72_PATH,
     f"{R72_PATH} N_ROUNDS=2 disagrees with 1 pairs"),
    ("pair arity", _pairs_source([("a", "b", "c")]), R72_PATH,
     f"{R72_PATH} PAIRS[0] is not a 2-tuple"),
    ("arm arity", _pairs_source([(SIX, SIX[:5])]), R72_PATH,
     f"{R72_PATH} PAIRS[0] arms are not 6-string tuples"),
)


def _write_tree(dest, replacements):
    for name in (CATALOG_NAME, PAIRS_NAME):
        (dest / name).write_bytes(replacements.get(name, _committed(name)))
    return dest / CATALOG_NAME


class SirLoaderRefusals(unittest.TestCase):
    def test_each_edit_raises_its_exact_refusal(self):
        for label, replacements, message in LOADER_CASES:
            with self.subTest(label), tempfile.TemporaryDirectory() as temp:
                header = _write_tree(Path(temp), replacements)
                with self.assertRaises(ValueError) as caught:
                    load_catalog(header)
                self.assertEqual(str(caught.exception), message)


class SirExtractRefusals(unittest.TestCase):
    def test_each_source_raises_its_exact_refusal(self):
        for label, source, path, message in EXTRACT_CASES:
            with self.subTest(label), self.assertRaises(ValueError) as caught:
                extract_mill_catalog(source, path=path)
            self.assertEqual(str(caught.exception), message)

    def test_unowned_mill_ids_name_their_home(self):
        cases = (
            ("sir-mill-r31", "home mill catalogs belong to the search package"),
            ("sir-mill-leftover9", "unknown sir leftover mill 'sir-mill-leftover9'"),
        )
        for mill_id, message in cases:
            with self.subTest(mill_id), self.assertRaises(ValueError) as caught:
                mill_kind_for_id(mill_id)
            self.assertEqual(str(caught.exception), message)

    def test_inert_statements_and_annotated_helpers_stay_literal(self):
        source = (
            '"""\n\n   First real line.\n"""\npass\n'
            "def helper(value: int) -> str:\n    return str(value)\n"
            + _LEFTOVER_SNIPPET.split("'''", 2)[2]
        )
        found = extract_mill_catalog(source, path=R72_PATH)
        self.assertEqual((found["doc_first_line"], found["n_rows"]), ("First real line.", 1))

    def test_loader_path_skips_non_python_arguments(self):
        tree = ast.parse('SourceFileLoader("m", join("dir", "sibling.py"))')
        self.assertEqual(_literal_sibling_path(tree), "experiments/sibling.py")

    def test_non_negative_unary_operators_and_non_module_docstrings(self):
        self.assertIs(literal_value(ast.parse("+1", mode="eval").body), UNSET)
        self.assertEqual(module_docstring(ast.parse("1", mode="eval")), "")


class SirCatalogWriter(unittest.TestCase):
    def test_writer_replaces_both_files_and_leaves_no_staging_files(self):
        mills = [extract_mill_catalog(_LEFTOVER_SNIPPET, path=R72_PATH)]
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp)
            write_catalog_files(mills, dest)
            names = sorted(path.name for path in dest.iterdir())
            catalog_text = (dest / CATALOG_NAME).read_text(encoding="utf-8")
            pairs_text = (dest / PAIRS_NAME).read_text(encoding="utf-8")
        self.assertEqual(names, [CATALOG_NAME, PAIRS_NAME])
        self.assertEqual(catalog_text, dumps_catalog(catalog_document(mills)))
        self.assertEqual(pairs_text, dumps_pairs(mills))


class SirIdentityHelpers(unittest.TestCase):
    def test_vendor_names_need_python_and_a_reviewed_prefix(self):
        cases = (("sir-mill.txt", False), ("notes.py", False), ("sir_r9_mill.py", True),
                 ("sir_extra_mill.py", True))
        for name, expected in cases:
            with self.subTest(name):
                self.assertIs(is_vendor_filename(name), expected)
        self.assertIsNone(refuse_vendor_paths(["notes.py", Path("docs/sir.md")]))
        self.assertEqual(forbidden_globs(), FORBIDDEN_MILL_GLOBS)

    def test_source_lookup_by_id(self):
        self.assertEqual(source_by_id("sir_r108_leftover3d_mill").path, R108_PATH)
        with self.assertRaises(KeyError) as caught:
            source_by_id("missing")
        self.assertEqual(caught.exception.args, ("unknown sir mill source 'missing'",))


if __name__ == "__main__":
    unittest.main()
