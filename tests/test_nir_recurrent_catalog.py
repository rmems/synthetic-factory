"""The shipped cycle probe must exercise the ordering policy it names."""

import json
from pathlib import Path
import unittest

import nir_equivalence as nir
from nir_equivalence_compare_pair import relevant_conventions

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL = ROOT / "tests/fixtures/parity-history/0bbeb5e6/nir-cross-runtime-equivalence/batch-r01.jsonl"


def historical_cycle():
    records = map(json.loads, HISTORICAL.read_text().splitlines())
    return next(record for record in records if record["scenario"]["id"] == "nir-recurrent-cycle")


class RecurrentCatalog(unittest.TestCase):
    def test_generated_catalog_runtimes_cut_different_cycle_edges(self):
        record = next(row for row in nir.generate_records(steps=12)
                      if row["scenario"]["id"] == "nir-recurrent-cycle")
        outputs = [entry["outputs"] for entry in record["oracle"]["runtimes"]
                   if entry["status"] == "executed"]
        self.assertEqual(len(outputs), 2)
        self.assertNotEqual(outputs[0]["evaluation_order"], outputs[1]["evaluation_order"])
        self.assertNotEqual(outputs[0]["recurrent_edges"], outputs[1]["recurrent_edges"])
        causes = record["result"]["comparison"]["attribution"]["candidate_reason_codes"]
        self.assertIn("DIVERGENCE_RECURRENT_ORDER", causes)
        self.assertEqual(nir.validate_record(record, "generated"), [])

    def test_identical_observed_cycle_cuts_do_not_support_order_attribution(self):
        old = historical_cycle()
        relevant = relevant_conventions(old["scenario"]["graph"], old["oracle"]["runtimes"])
        self.assertNotIn("cycle_break_order", relevant)
        self.assertIn("reset", relevant)

    def test_obsolete_cycle_recipe_is_preserved_but_not_validated_as_current(self):
        errors = nir.validate_record(historical_cycle(), "historical")
        self.assertTrue(any("scenario.graph does not match" in error for error in errors), errors)
