"""Pin pay Archive B literal reading: which plant fragments are literals, which rows count.

``archive_b_extract`` reads ``mill_plants.py`` without executing it. These
cases cover every fragment shape ``_const_eval`` accepts or refuses, and the
rule that only top-level ``PAIRS.append`` statements become catalog rows.
"""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from pay import archive_b_extract as extract
from pay._contract import FINDING_AST_NOT_A_PAIR, FINDING_SOURCE_NOT_PARSEABLE, PayRefusal


def _fragment(expression: str) -> ast.expr:
    return ast.parse(expression, mode="eval").body


def _row(ok: str, fail: str) -> str:
    return f"PAIRS.append((_ok(slug={ok!r}), _fail(slug={fail!r})))\n"


class ConstEvalTests(unittest.TestCase):
    def test_literal_fragments_evaluate(self) -> None:
        cases = {
            "7": 7,
            "-2.5": -2.5,
            "-(-3)": 3,
            "'text'": "text",
            "f'a{1}b{-2}c'": "a1b-2c",
            "f'{1:>3}'": "1",
            "f'{[1, 2]}'": "[1, 2]",
            "f''": "",
            "[1, (2, -3)]": [1, (2, -3)],
            "()": (),
            "{'a': [-1, None], 2: 'b'}": {"a": [-1, None], 2: "b"},
            "{}": {},
            "dict()": {},
            "dict(a=1, b=_ok(c='x'))": {"a": 1, "b": {"c": "x"}},
            "_fail(slug=f'x{2}', tags=['t'])": {"slug": "x2", "tags": ["t"]},
        }
        for expression, expected in cases.items():
            with self.subTest(expression=expression):
                self.assertEqual(extract._const_eval(_fragment(expression)), expected)

    def test_non_literal_fragments_are_refused(self) -> None:
        for expression in (
            "+1",
            "not 1",
            "~1",
            "name",
            "1 + 2",
            "{1}",
            "[*items]",
            "f'{name}'",
            "foo(a=1)",
            "module.dict(a=1)",
            "dict(1)",
            "_ok(*args)",
            "dict(**kwargs)",
            "_fail(a=1, **kwargs)",
            "dict(a=1)(b=2)",
        ):
            with self.subTest(expression=expression):
                with self.assertRaises(PayRefusal) as caught:
                    extract._const_eval(_fragment(expression))
                self.assertEqual(caught.exception.code, FINDING_AST_NOT_A_PAIR)
                self.assertIn("non-literal plant fragment", caught.exception.message)

    def test_an_fstring_piece_that_is_neither_text_nor_a_value_adds_nothing(self) -> None:
        node = ast.JoinedStr(values=[ast.Constant("a"), ast.Name("ignored"), ast.Constant("b")])
        self.assertEqual(extract._const_eval(node), "ab")

    def test_dict_unpacking_is_refused_before_any_value_is_read(self) -> None:
        for expression in ("{**extra}", "{'a': name, **extra}"):
            with self.subTest(expression=expression):
                with self.assertRaises(PayRefusal) as caught:
                    extract._const_eval(_fragment(expression))
                self.assertEqual(caught.exception.code, FINDING_AST_NOT_A_PAIR)
                self.assertTrue(caught.exception.message.endswith("uses dict unpacking"))


class PairsFromSourceTests(unittest.TestCase):
    def test_only_top_level_pairs_appends_become_rows(self) -> None:
        source = (
            "PAIRS = []\n"
            "print('not a row')\n"
            "PAIRS\n"
            "PAIRS.append\n"
            + _row("first-ok", "first-fail")
            + "MORE.append((_ok(slug='more-ok'), _fail(slug='more-fail')))\n"
            "lane.PAIRS.append((_ok(slug='attr-ok'), _fail(slug='attr-fail')))\n"
            "PAIRS.extend([])\n"
            "if True:\n"
            "    " + _row("nested-ok", "nested-fail")
            + _row("second-ok", "second-fail")
        )
        rows = extract.pairs_from_source(source, source="plants.py")
        self.assertEqual(
            [(row["ok"]["slug"], row["fail"]["slug"]) for row in rows],
            [("first-ok", "first-fail"), ("second-ok", "second-fail")],
        )

    def test_source_without_pairs_appends_is_refused(self) -> None:
        for source in ("", "PAIRS = []\n", "MORE.append((_ok(slug='a'), _fail(slug='b')))\n"):
            with self.subTest(source=source):
                with self.assertRaises(PayRefusal) as caught:
                    extract.pairs_from_source(source, source="plants.py")
                self.assertEqual(caught.exception.code, FINDING_SOURCE_NOT_PARSEABLE)
                self.assertEqual(caught.exception.message, "plants.py has no PAIRS.append rows")

    def test_a_non_literal_row_refuses_the_whole_source(self) -> None:
        source = _row("ok", "fail") + "PAIRS.append((_ok(slug=name), _fail(slug='b')))\n"
        with self.assertRaises(PayRefusal) as caught:
            extract.pairs_from_source(source, source="plants.py")
        self.assertEqual(caught.exception.code, FINDING_AST_NOT_A_PAIR)


if __name__ == "__main__":
    unittest.main()
