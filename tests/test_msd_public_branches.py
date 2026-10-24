"""MSD fail-closed branches reached through the public surface only.

``load_catalog`` on mutated temp copies of ``config/msd``, ``plants_from_source``
on small in-memory sources, and ``generate.run`` into temp destinations.
"""

from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
support = importlib.import_module("mill_public_branch_support")
catalog = importlib.import_module("msd.catalog")
generate = importlib.import_module("msd.generate")
MsdRefusal = importlib.import_module("msd._contract").MsdRefusal

COMMITTED = support.REPO / "config" / "msd"
INVALID, UNPARSEABLE = "msd.plant_field_invalid", "msd.source_not_parseable"
# One keyword-only r747 ``P(...)`` carrying every r747 field.
ONE_PAIR = (
    "PAIRS = [P(slug='s', old='o', new='n', keep='k', dead='d', residual='r', extra='e', "
    "freeze='f', family='fa', reject='rj', method='m', peer='p', ticket='t', canon='c', "
    "wid='w', test_ok='to', falseg='fg', map_fn='mf', success=True)]\n"
)


def extract(text: str, mill_id: str = "msd_r0005", **kwargs):
    return catalog.plants_from_source(text, mill_id=mill_id, source="s.py", **kwargs)


def source_refusal(text: str, mill_id: str = "msd_r0005", **kwargs):
    return support.refusal(MsdRefusal, extract, text, mill_id, **kwargs)


class MsdCatalogContract(support.SiblingCatalogContract, unittest.TestCase):
    catalog = catalog
    error_type = MsdRefusal
    prefix = "msd"
    committed = COMMITTED
    pins_unregistered_factory = True

    def test_the_default_catalog_is_the_committed_one(self):
        self.assertEqual(catalog.default_catalog_dir(), COMMITTED)


class MsdGenerateContract(support.SiblingGenerateContract, unittest.TestCase):
    generate = generate
    error_type = MsdRefusal
    prefix = "msd"
    committed = COMMITTED

    def test_a_long_decision_basis_is_clipped_to_240_characters(self):
        copy = support.one_plant_copy(self, COMMITTED, leftover="x" * 300)
        records = support.generated_records(self, generate, copy.directory)
        basis = records[0]["steps"][0]["decision_basis"]
        self.assertEqual((len(basis), basis[-1]), (240, "…"))
        self.assertTrue(basis.startswith("Plan: locate Map xxx"), basis)


class MsdSourceShapes(unittest.TestCase):
    def test_malformed_sources_are_coded_refusals(self):
        for label, text, expected in (
            ("empty pairs", "PAIRS = []\n", (UNPARSEABLE, "s.py has no PAIRS/PLANTS list")),
            ("scalar plants", "PLANTS = 3\n", (UNPARSEABLE, "s.py has no PAIRS/PLANTS list")),
            ("tuple start", "START = (1,)\n" + ONE_PAIR,
             (INVALID, "BASE/START must be a positive int")),
            ("text success", ONE_PAIR.replace("success=True", "success='yes'"),
             (INVALID, "s.py PAIRS[0].success must be a bool")),
        ):
            with self.subTest(label):
                self.assertEqual(source_refusal(text), expected)

    def test_the_mill_id_and_an_explicit_round_are_checked(self):
        for label, kwargs, expected in (
            ("mill id", {"mill_id": "msd-5"}, (INVALID, "mill_id 'msd-5' is not msd_rNNN")),
            ("explicit round", {"base_round": 0}, (INVALID, "s.py BASE must be a positive int")),
        ):
            with self.subTest(label):
                self.assertEqual(source_refusal(ONE_PAIR, **kwargs), expected)

    def test_a_syntax_error_is_a_coded_refusal(self):
        code, message = source_refusal("PAIRS = [\n")
        self.assertEqual(code, UNPARSEABLE)
        self.assertTrue(message.startswith("s.py does not parse: "), message)

    def test_statements_that_bind_no_single_name_are_skipped(self):
        rows = extract("import os\na = b = 1\nobj.attr = 2\nSTART: int\n" + ONE_PAIR)
        identity = [(row["plant_id"], row["base_round"], row["repo"]) for row in rows]
        self.assertEqual(identity, [("msd_r0005:s", 5, "repo-mcp")])


if __name__ == "__main__":
    unittest.main()
