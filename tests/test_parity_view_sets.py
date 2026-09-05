"""Tests for pipelines/oracle_grounded/parity_view_sets.py -- view-set authentication."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from parity_contract_support import contract, make_record, make_view  # noqa: E402


class ViewSets(unittest.TestCase):
    """The view set must be a faithful one-to-one image of the record set."""

    def test_dropping_a_whole_record_from_the_view_set_is_rejected(self):
        passing = make_record(id="rec-pass")
        failing = make_record(id="rec-fail")
        failing["result"]["verdict"] = contract.VERDICT_MISMATCH
        views = [make_view(passing)]
        errors = contract.view_set_errors([passing, failing], views)
        self.assertTrue(any("rec-fail" in error for error in errors))

    def test_complete_view_set_passes(self):
        records = [make_record(id="rec-a"), make_record(id="rec-b")]
        views = [make_view(record) for record in records]
        self.assertEqual(contract.view_set_errors(records, views), [])

    def test_duplicating_a_view_reweights_the_corpus_and_is_rejected(self):
        # Repeating the agreeable half dilutes failures as effectively as
        # deleting them.
        passing = make_record(id="rec-pass")
        failing = make_record(id="rec-fail")
        failing["result"]["verdict"] = contract.VERDICT_MISMATCH
        records = [passing, failing]
        views = [make_view(passing), make_view(passing), make_view(failing)]
        errors = contract.view_set_errors(records, views)
        self.assertTrue(any("repeats" in error for error in errors))

    def test_a_view_with_no_record_behind_it_is_rejected(self):
        records = [make_record(id="rec-a")]
        views = [make_view(records[0]), make_view(make_record(id="rec-invented"))]
        errors = contract.view_set_errors(records, views)
        self.assertTrue(any("rec-invented" in error for error in errors))

    def test_non_string_view_id_is_rejected_explicitly(self):
        errors = contract.view_set_errors([], [{"id": None}])
        self.assertTrue(
            any("invalid non-string view IDs" in error for error in errors),
            errors,
        )

    def test_unhashable_source_record_id_is_reported_not_raised(self):
        # An unhashable id (e.g. a list) must not reach `in` on the
        # view_id_counts dict, which raises TypeError for unhashable keys.
        errors = contract.view_set_errors([{"id": []}], [])
        self.assertTrue(
            any("invalid non-string IDs" in error for error in errors), errors
        )


if __name__ == "__main__":
    unittest.main()
