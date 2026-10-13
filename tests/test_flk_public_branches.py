"""FLK fail-closed branches reached through the public surface only.

``load_catalog`` on mutated temp copies of ``config/flk``, ``plants_from_source``
on small in-memory sources, and ``generate.run`` into temp destinations.
"""

from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
support = importlib.import_module("mill_public_branch_support")
catalog = importlib.import_module("flk.catalog")
generate = importlib.import_module("flk.generate")
FlkRefusal = importlib.import_module("flk._contract").FlkRefusal

COMMITTED = support.REPO / "config" / "flk"
PLANT = support.source_plant(COMMITTED, slug="tiny-clock")


def source_refusal(text: str) -> tuple[str, str] | None:
    return support.refusal(
        FlkRefusal, catalog.plants_from_source, text, mill_id="flk_r0003", source="s.py"
    )


class FlkCatalogContract(support.SiblingCatalogContract, unittest.TestCase):
    catalog = catalog
    error_type = FlkRefusal
    prefix = "flk"
    committed = COMMITTED


class FlkGenerateContract(support.SiblingGenerateContract, unittest.TestCase):
    generate = generate
    error_type = FlkRefusal
    prefix = "flk"
    committed = COMMITTED


class FlkSourceShapes(unittest.TestCase):
    def test_malformed_plants_are_coded_refusals(self):
        for label, text, expected in (
            ("tuple plant", "PLANTS = [('x',)]\n",
             ("flk.source_not_parseable", "s.py PLANTS[0] is not an object")),
            ("missing key", "PLANTS = [{'slug': 'x'}]\n",
             ("flk.plant_field_missing", "s.py PLANTS[0] missing runner")),
        ):
            with self.subTest(label):
                self.assertEqual(source_refusal(text), expected)

    def test_a_syntax_error_is_a_coded_refusal(self):
        code, message = source_refusal("PLANTS = [\n")
        self.assertEqual(code, "flk.source_not_parseable")
        self.assertTrue(message.startswith("s.py does not parse: "), message)

    def test_statements_that_bind_no_single_name_are_skipped(self):
        text = f"a = b = 1\nobj.attr = 2\nPLANTS: list\nPLANTS = [{PLANT!r}]\n"
        rows = catalog.plants_from_source(text, mill_id="flk_r0003", source="s.py")
        identity = [(row["plant_id"], row["base_round"]) for row in rows]
        self.assertEqual(identity, [("flk_r0003:tiny-clock", 3)])

    def test_the_default_catalog_is_the_committed_one(self):
        self.assertEqual(catalog.default_catalog_dir(), COMMITTED)


if __name__ == "__main__":
    unittest.main()
