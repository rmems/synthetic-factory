"""SAF fail-closed branches reached through the public surface only.

``load_catalog`` on mutated temp copies of ``config/saf``, ``plants_from_source``
on small in-memory sources, and ``generate.run`` into temp destinations.
"""

from __future__ import annotations

import importlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
support = importlib.import_module("mill_public_branch_support")
catalog = importlib.import_module("saf.catalog")
generate = importlib.import_module("saf.generate")
SafRefusal = importlib.import_module("saf._contract").SafRefusal

COMMITTED = support.REPO / "config" / "saf"
PAIR = support.source_plant(COMMITTED, flavor="tool-output", slug="sops")
MILL = "saf_r0005"


def source_refusal(text: str, mill_id: str = MILL) -> tuple[str, str] | None:
    return support.refusal(
        SafRefusal, catalog.plants_from_source, text, mill_id=mill_id, source="s.py"
    )


class SafCatalogContract(support.SiblingCatalogContract, unittest.TestCase):
    catalog = catalog
    error_type = SafRefusal
    prefix = "saf"
    committed = COMMITTED
    pins_unregistered_factory = True

    def test_a_plant_row_needs_a_saf_flavor(self):
        row = json.loads(self.committed_lines()[0])
        payload = support.compact_jsonl([{**row, "flavor": "nope"}])
        expected = ("saf.plant_field_invalid", "plants.jsonl:1.flavor is not a saf flavor")
        self.assertEqual(self.rows_refusal(payload, plant_count=1), expected)


class SafGenerateContract(support.SiblingGenerateContract, unittest.TestCase):
    generate = generate
    error_type = SafRefusal
    prefix = "saf"
    committed = COMMITTED

    def test_a_miss_id_over_80_characters_drops_the_flavor(self):
        slug = "s" * 70
        changes = {"slug": slug, "plant_id": f"saf_r5045:{slug}", "flavor": "tool-output"}
        copy = support.one_plant_copy(self, COMMITTED, **changes)
        records = support.generated_records(self, generate, copy.directory)
        ids = [record["id"] for record in records]
        self.assertEqual(ids, [f"saf-r5045-{slug}", f"saf-r5045-miss-{slug}"])


class SafSourceShapes(unittest.TestCase):
    def test_malformed_sources_are_coded_refusals(self):
        for label, text, mill_id, expected in (
            ("tuple pair", "PAIRS = [('x',)]\n", MILL,
             ("saf.source_not_parseable", "s.py PAIRS[0] is not an object")),
            ("mill id", f"PAIRS = [{PAIR!r}]\n", "saf-5",
             ("saf.plant_field_invalid", "mill_id 'saf-5' is not saf_rNNN")),
        ):
            with self.subTest(label):
                self.assertEqual(source_refusal(text, mill_id), expected)

    def test_a_syntax_error_is_a_coded_refusal(self):
        code, message = source_refusal("PAIRS = [\n")
        self.assertEqual(code, "saf.source_not_parseable")
        self.assertTrue(message.startswith("s.py does not parse: "), message)

    def test_statements_that_bind_no_single_name_are_skipped(self):
        text = f"a = b = 1\nobj.attr = 2\nPAIRS: list\nPAIRS = [{PAIR!r}]\n"
        rows = catalog.plants_from_source(text, mill_id=MILL, source="s.py")
        identity = [(row["plant_id"], row["base_round"]) for row in rows]
        self.assertEqual(identity, [("saf_r0005:sops", 5)])

    def test_the_default_catalog_is_the_committed_one(self):
        self.assertEqual(catalog.default_catalog_dir(), COMMITTED)


if __name__ == "__main__":
    unittest.main()
