"""Pin ``qbp.catalog_ast``: literal reading, plants pointers and catalog assembly.

``ast_extract_catalog`` is driven offline by pointing its pinned source table
at one synthetic mill/plants pair whose digests match, so every pin, pointer
and window refusal runs without the legacy ref.
"""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from qbp import catalog_ast as ca
from qbp._contract import BAN, FACTORY, FAMILY_PREFIX, QbpRefusal
from qbp.plants import BAD_ARG_NAMES, OK_ARG_NAMES

_MILL = (
    f"FACTORY = {FACTORY!r}\nPREFIX = {FAMILY_PREFIX!r}\nBAN = {sorted(BAN)!r}\n"
    "plants = SourceFileLoader('plants', str(ROOT / 'qbp-plants-fixture.py')).load_module()\n"
)


def _ctor(name: str, args: tuple[str, ...], tag: str) -> str:
    return f"{name}(" + ", ".join(repr(f"{tag}-{arg}") for arg in args) + ")"


_PLANTS = (
    "CATALOG_FIRST = 7\nPAIRS = [\n"
    f"    ({_ctor('_ok', OK_ARG_NAMES, 'a')}, {_ctor('_bad', BAD_ARG_NAMES, 'b')}),\n"
    "]\n"
)


def _extract(mill: str = _MILL, plants: str = _PLANTS, *, first: int = 7, n_pairs: int = 1):
    source = (
        "qbp-mill-fixture",
        "experiments/qbp-mill-fixture.py",
        ca.sha256_text(mill),
        "experiments/qbp-plants-fixture.py",
        ca.sha256_text(plants),
        first,
        n_pairs,
    )
    with (
        mock.patch.object(ca, "MILL_SOURCES", (source,)),
        mock.patch.object(ca, "N_MILLS", 1),
        mock.patch.object(ca, "N_PAIRS", 1),
    ):
        return ca.ast_extract_catalog({source[1]: mill}, {source[3]: plants}, commit="c0ffee")


class CatalogAssemblyTests(unittest.TestCase):
    def test_one_pinned_mill_yields_its_entry_and_pairs(self):
        document = _extract()
        self.assertEqual(document["source"], {"lane": ca.LEGACY_LANE, "commit": "c0ffee"})
        self.assertEqual(
            document["mills"],
            [
                {
                    "mill_id": "qbp-mill-fixture",
                    "path": "experiments/qbp-mill-fixture.py",
                    "sha256": ca.sha256_text(_MILL),
                    "plants": "experiments/qbp-plants-fixture.py",
                    "plants_sha256": ca.sha256_text(_PLANTS),
                    "catalog_first": 7,
                    "n_pairs": 1,
                    "ban": sorted(BAN),
                }
            ],
        )
        (pair,) = document["pairs"]
        self.assertEqual((pair["mill_id"], pair["round"]), ("qbp-mill-fixture", 7))
        self.assertEqual(pair["ok"]["slug"], "a-slug")
        self.assertEqual(pair["bad"]["ticket_why"], "b-ticket_why")

    def test_pointer_and_window_drift_are_refused(self):
        moved = _MILL.replace("qbp-plants-fixture.py", "qbp-plants-other.py")
        with self.assertRaises(QbpRefusal) as caught:
            _extract(moved)
        self.assertIn("plants pointer 'experiments/qbp-plants-other.py'", str(caught.exception))
        for first, n_pairs in ((8, 1), (7, 2)):
            with self.subTest(first=first, n_pairs=n_pairs), self.assertRaises(QbpRefusal) as caught:
                _extract(first=first, n_pairs=n_pairs)
            self.assertIn("catalog window 7+1", str(caught.exception))


class LiteralTests(unittest.TestCase):
    @staticmethod
    def _literal(expr: str):
        return ca._literal(ast.parse(expr, mode="eval").body, "w")

    def test_supported_literals(self):
        cases = (
            ("[1, (2, -3.5), {4}]", [1, [2, -3.5], [4]]),
            ("{'a': None, 'b': +2}", {"a": None, "b": 2}),
            ("-(-3)", 3),
        )
        for expr, expected in cases:
            with self.subTest(expr=expr):
                self.assertEqual(self._literal(expr), expected)

    def test_unsupported_nodes_and_operands_are_refused(self):
        cases = (
            ("b'x'", "w: unsupported Constant"),
            ("name", "w: unsupported Name"),
            ("-'a'", "w: unary operand must be a number"),
            ("-True", "w: unary operand must be a number"),
            ("{**d}", "w: starred dict"),
        )
        for expr, message in cases:
            with self.subTest(expr=expr), self.assertRaises(QbpRefusal) as caught:
                self._literal(expr)
            self.assertTrue(str(caught.exception).endswith(message), str(caught.exception))


class PlantsPointerTests(unittest.TestCase):
    def test_only_str_of_a_division_by_a_literal_names_the_plants_file(self):
        cases = (
            ("str(ROOT / 'plants.py')", "plants.py"),
            ("str(ROOT + 'plants.py')", None),
            ("str()", None),
            ("repr(ROOT / 'plants.py')", None),
            ("mod.str(ROOT / 'plants.py')", None),
            ("str(ROOT / NAME)", None),
        )
        for expr, expected in cases:
            with self.subTest(expr=expr):
                self.assertEqual(ca._plants_filename(ast.parse(expr, mode="eval").body), expected)


if __name__ == "__main__":
    unittest.main()
