"""RAG fail-closed branches reached through the public surface only.

``load_catalog`` on mutated temp copies of ``config/rag``, ``plants_from_source``
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
catalog = importlib.import_module("rag.catalog")
generate = importlib.import_module("rag.generate")
RagRefusal = importlib.import_module("rag._contract").RagRefusal

COMMITTED = support.REPO / "config" / "rag"
P_CALL = "P('qdrant', 'payload', 'QD-1', 'QD-2')"
UNPARSEABLE = "rag.source_not_parseable"
POSITIONAL = "P() must be four positional literals"


def source_refusal(text: str) -> tuple[str, str] | None:
    return support.refusal(
        RagRefusal, catalog.plants_from_source, text, mill_id="rag_r0005", source="s.py"
    )


class RagCatalogContract(support.SiblingCatalogContract, unittest.TestCase):
    catalog = catalog
    error_type = RagRefusal
    prefix = "rag"
    committed = COMMITTED

    def test_a_plant_row_needs_rag_ids(self):
        row = json.loads(self.committed_lines()[0])
        for label, key, value, message in (
            ("mill id", "mill_id", "x_1", "plants.jsonl:1.mill_id is not rag_rNNN"),
            ("slug", "slug", "-bad", "plants.jsonl:1.slug is not a plant slug"),
        ):
            with self.subTest(label):
                payload = support.compact_jsonl([{**row, key: value}])
                expected = ("rag.plant_field_invalid", message)
                self.assertEqual(self.rows_refusal(payload, plant_count=1), expected)


class RagGenerateContract(support.SiblingGenerateContract, unittest.TestCase):
    generate = generate
    error_type = RagRefusal
    prefix = "rag"
    committed = COMMITTED

    def test_a_long_decision_basis_is_clipped_to_240_characters(self):
        eng = "q" * 300
        changes = {"eng": eng, "slug": f"{eng}-payload", "plant_id": f"rag_r670:{eng}-payload"}
        copy = support.one_plant_copy(self, COMMITTED, **changes)
        records = support.generated_records(self, generate, copy.directory)
        basis = records[0]["steps"][0]["decision_basis"]
        self.assertEqual((len(basis), basis[-1]), (240, "…"))
        self.assertTrue(basis.startswith("Plan: list leftover leftover leftover qqq"), basis)


class RagSourceShapes(unittest.TestCase):
    def test_malformed_pairs_are_coded_refusals(self):
        for label, text, expected in (
            ("text item", "PAIRS = ['x']\n",
             (UNPARSEABLE, "s.py PAIRS[0] is not a P() literal call")),
            ("keywords", "PAIRS = [P(eng='a')]\n", (UNPARSEABLE, POSITIONAL)),
            ("starred", "PAIRS = [P(*row)]\n", (UNPARSEABLE, POSITIONAL)),
            ("three args", "PAIRS = [P('a', 'b', 'c')]\n",
             (UNPARSEABLE, "P() must have four arguments")),
            ("duplicate", f"PAIRS = [{P_CALL}, {P_CALL}]\n",
             ("rag.plant_duplicate_id", "s.py duplicate rag_r0005:qdrant-payload")),
        ):
            with self.subTest(label):
                self.assertEqual(source_refusal(text), expected)

    def test_a_syntax_error_is_a_coded_refusal(self):
        code, message = source_refusal("PAIRS = [\n")
        self.assertEqual(code, UNPARSEABLE)
        self.assertTrue(message.startswith("s.py does not parse: "), message)

    def test_statements_that_bind_no_single_name_are_skipped(self):
        text = f"a = b = 1\nobj.attr = 2\nPAIRS: list\nPAIRS = [{P_CALL}]\n"
        rows = catalog.plants_from_source(text, mill_id="rag_r0005", source="s.py")
        identity = [(row["plant_id"], row["base_round"]) for row in rows]
        self.assertEqual(identity, [("rag_r0005:qdrant-payload", 5)])

    def test_the_default_catalog_is_the_committed_one(self):
        self.assertEqual(catalog.default_catalog_dir(), COMMITTED)


class RagRoundsAndSelectors(unittest.TestCase):
    def test_plant_for_round_cycles_from_the_first_mill_base(self):
        loaded = catalog.load_catalog(COMMITTED)
        base, plants = loaded.mills[0].base_round, loaded.plants
        rounds = (base, base + len(plants) + 1, base - 1)
        found = [loaded.plant_for_round(rnd) for rnd in rounds]
        self.assertEqual(found, [plants[0], plants[1], plants[-1]])

    def test_plant_for_round_refuses_a_catalog_without_plants(self):
        empty = catalog.Catalog(
            catalog_id="rag-empty", directory=COMMITTED, factory="f", plants_sha256="0",
            plants=(), mills=(), meta={},
        )
        expected = ("rag.plant_not_found", "catalog has no plants")
        self.assertEqual(support.refusal(RagRefusal, empty.plant_for_round, 670), expected)

    def test_the_mill_selector_matches_every_plant_on_a_one_mill_catalog(self):
        root = support.temp_dir(self)
        by_mill = generate.run(generate.GenerateRequest(COMMITTED, root / "m", mill_id="rag_r670"))
        every = generate.run(generate.GenerateRequest(COMMITTED, root / "a", all_plants=True))
        found = (by_mill["records"], by_mill["records_sha256"])
        self.assertEqual(found, (32, every["records_sha256"]))


if __name__ == "__main__":
    unittest.main()
