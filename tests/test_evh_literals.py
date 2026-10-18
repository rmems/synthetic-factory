"""EVH literal resolver and compact-JSONL row checks.

``catalog_ast.resolve`` must evaluate only its closed set of literal forms and
leave everything else ``UNSET``; ``_jsonl_rows`` must refuse every framing and
row-shape drift with the caller's own wording.
"""

from __future__ import annotations

import ast
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from evh import _jsonl_rows as rows
from evh import catalog_ast
from evh.catalog_extract import sha256_bytes
from evh.vocabulary import LEFTOVER_PLANT_ROW_KEYS

UNSET = catalog_ast.UNSET
ENV = {"name": "mill", "n": 7, "items": ["a", "b", "c"], "table": {"k": "v"}, "flag": True}


def _resolve(expr: str):
    return catalog_ast.resolve(ast.parse(expr, mode="eval").body, ENV)


class ResolveTests(unittest.TestCase):
    def test_closed_literal_forms_resolve(self):
        cases = {
            "'x'": "x",
            "name": "mill",
            "-n": -7,
            "-2.5": -2.5,
            "(1, n)": (1, 7),
            "[name, 'b']": ["mill", "b"],
            "{n}": {7},
            "{'a': n}": {"a": 7},
            "f'{name}-{n}'": "mill-7",
            "f'{name!s}'": "mill",
            "'a' + 'b'": "ab",
            "n + 1": 8,
            "n - 2": 5,
            "n // 2": 3,
            "items[1]": "b",
            "items[1:]": ["b", "c"],
            "items[::2]": ["a", "c"],
            "table['k']": "v",
            "pair('a', n)": ("a", 7),
            "name.upper()": "MILL",
            "name.title()": "Mill",
            "'a-b'.replace('-', '_')": "a_b",
        }
        for expr, expected in cases.items():
            with self.subTest(expr=expr):
                self.assertEqual(_resolve(expr), expected)

    def test_everything_else_stays_unset(self):
        cases = [
            "missing",
            "not flag",
            "-name",
            "(1, missing)",
            "{missing}",
            "{**table}",
            "{'a': missing}",
            "{missing: 1}",
            "f'{n:>3}'",
            "f'{name!r}'",
            "f'{items}'",
            "f'{missing}'",
            "missing + 1",
            "'a' + 1",
            "n * 2",
            "'a' - 'b'",
            "missing[0]",
            "items[missing]",
            "items[9]",
            "table['nope']",
            "items[missing:]",
            "exec('1')",
            "eval('1')",
            "compile('1', 'x', 'eval')",
            "__import__('os')",
            "pair(missing)",
            "pair(n, key=1)",
            "name.strip()",
            "missing.upper()",
            "n.upper()",
            "name.replace(missing, 'b')",
            "name.replace('a', 1)",
            "name.upper(1)",
            "len(items)",
            "lambda: 1",
        ]
        for expr in cases:
            with self.subTest(expr=expr):
                self.assertIs(_resolve(expr), UNSET)

    def test_floor_division_by_zero_still_raises(self):
        with self.assertRaises(ZeroDivisionError):
            _resolve("n // 0")

    def test_every_slice_bound_is_resolved_before_refusing(self):
        with self.assertRaises(ZeroDivisionError):
            _resolve("items[missing:1 // 0]")

    def test_require_names_the_context_and_line(self):
        node = ast.parse("\n\nmissing", mode="eval").body
        with self.assertRaises(ValueError) as caught:
            catalog_ast.require(node, ENV, "catalog:row")
        self.assertEqual(str(caught.exception), "catalog:row: cannot resolve AST at line 3")
        self.assertEqual(catalog_ast.require(ast.parse("n", mode="eval").body, ENV, "x"), 7)


def _plant(**overrides) -> dict:
    row = {key: f"{key}-value" for key in LEFTOVER_PLANT_ROW_KEYS}
    row["index"] = 0
    row.update(overrides)
    return row


class JsonlFramingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "rows.jsonl"

    def test_lf_framed_text_is_returned(self):
        self.path.write_bytes(b'{"a":1}\n')
        self.assertEqual(rows.read_lf_jsonl(self.path, "cannot read"), '{"a":1}\n')

    def test_missing_trailing_newline_is_refused(self):
        self.path.write_bytes(b'{"a":1}')
        with self.assertRaises(ValueError) as caught:
            rows.read_lf_jsonl(self.path, "cannot read")
        self.assertEqual(str(caught.exception), "rows.jsonl must be LF-framed jsonl")

    def test_unreadable_file_uses_the_callers_wording(self):
        missing = self.path.with_name("absent.jsonl")
        with self.assertRaises(ValueError) as caught:
            rows.read_lf_jsonl(missing, "cannot read")
        self.assertTrue(str(caught.exception).startswith(f"cannot read {missing}: "))

    def test_parse_rows_numbers_lines_and_refuses_empty(self):
        parsed = rows.parse_rows("a\nb\n", "f.jsonl", lambda line, i, name: {name: (i, line)}, "empty")
        self.assertEqual(parsed, ({"f.jsonl": (1, "a")}, {"f.jsonl": (2, "b")}))
        with self.assertRaises(ValueError) as caught:
            rows.parse_rows("", "f.jsonl", lambda *_: {}, "has no rows")
        self.assertEqual(str(caught.exception), "f.jsonl has no rows")

    def test_require_pinned_binds_digest_then_count(self):
        text = "x\n"
        digest = sha256_bytes(text.encode())
        rows.require_pinned(text, [{}], "plants", (digest, 1))
        with self.assertRaises(ValueError) as caught:
            rows.require_pinned(text, [{}], "plants", ("0" * 64, 1))
        self.assertEqual(str(caught.exception), "plants sha256 drifted from vocabulary")
        with self.assertRaises(ValueError) as caught:
            rows.require_pinned(text, [{}], "plants", (digest, 2))
        self.assertEqual(str(caught.exception), "plants must contain 2 rows, found 1")


class JsonlRowTests(unittest.TestCase):
    def _refusal(self, line: str, source: str | None = None) -> str:
        with self.assertRaises(ValueError) as caught:
            rows.plant_row(line, "row 1", source)
        return str(caught.exception)

    def test_valid_plant_row_keeps_key_order(self):
        row = _plant(source="mill.py")
        parsed = rows.plant_row(json.dumps(row), "row 1", "mill.py")
        self.assertEqual(list(parsed), list(LEFTOVER_PLANT_ROW_KEYS))
        self.assertEqual(rows.plant_row(json.dumps(row), "row 1", None), parsed)

    def test_row_framing_refusals(self):
        cases = {
            "": "row 1 is not a compact JSONL row",
            ' {"a": 1}': "row 1 is not a compact JSONL row",
            "\t{}": "row 1 is not a compact JSONL row",
            "{nope": None,
            "[1]": "row 1 must be an object",
        }
        for line, message in cases.items():
            with self.subTest(line=line):
                got = self._refusal(line)
                if message is None:
                    self.assertTrue(got.startswith("row 1 is not JSON: "))
                else:
                    self.assertEqual(got, message)

    def test_row_key_and_field_refusals(self):
        extra = dict(_plant(), extra=1)
        missing = _plant()
        del missing["ok_slug"]
        self.assertEqual(
            self._refusal(json.dumps(extra)), "row 1 keys differ: missing=[] extra=['extra']"
        )
        self.assertEqual(
            self._refusal(json.dumps(missing)), "row 1 keys differ: missing=['ok_slug'] extra=[]"
        )
        for value in (True, "0", 1.0):
            with self.subTest(index=value):
                self.assertEqual(
                    self._refusal(json.dumps(_plant(index=value))), "row 1 index must be an int"
                )
        for value in ("", 3, None):
            with self.subTest(ok_slug=value):
                self.assertEqual(
                    self._refusal(json.dumps(_plant(ok_slug=value))),
                    "row 1 ok_slug must be a non-empty string",
                )
        self.assertEqual(
            self._refusal(json.dumps(_plant(source="other.py")), "mill.py"),
            "row 1 source must be mill.py",
        )


if __name__ == "__main__":
    unittest.main()
