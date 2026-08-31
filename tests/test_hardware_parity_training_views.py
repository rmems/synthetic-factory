"""Training views derived from hardware-parity records.

A training view must stay a faithful, oracle-backed image of the record it
came from; these tests pin that contract.
"""

import copy
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hardware_parity_support import (  # noqa: E402
    WHERE,
    fixture_records as _fixture_records,
)

import hardware_parity as hp  # noqa: E402
import neuro_oracle as oracle  # noqa: E402
import oracle_contract as contract  # noqa: E402

class TrainingViews(unittest.TestCase):
    def test_views_preserve_every_record(self):
        records = _fixture_records()
        views, errors = hp.build_training_views(records)
        self.assertEqual(errors, [])
        self.assertEqual(len(views), len(records))

    def test_failed_records_are_flagged_in_the_view(self):
        views, _ = hp.build_training_views(_fixture_records())
        failed = [view for view in views if view["parity_failed"]]
        self.assertTrue(failed)
        for view in failed:
            self.assertNotEqual(view["verdict"], contract.VERDICT_MATCH)
            self.assertTrue(view["reason_codes"])

    def test_view_names_both_execution_targets(self):
        views, _ = hp.build_training_views(_fixture_records())
        self.assertIn(oracle.TARGET_SOFTWARE_FLOAT, views[0]["execution_targets"])
        self.assertIn(
            oracle.TARGET_FIXED_POINT_MODEL, views[0]["execution_targets"]
        )

    def test_filtering_out_failures_is_rejected(self):
        records = _fixture_records()
        views = [
            hp.training_view(record)
            for record in records
            if record["result"]["verdict"] == contract.VERDICT_MATCH
        ]
        errors = contract.view_set_errors(records, views)
        self.assertTrue(any("TRAINING_VIEW_HIDES_FAILURE" in error for error in errors))

    def test_prefiltered_batch_fails_catalog_authentication(self):
        # The view/set checks compare views against the records they were
        # handed, which is vacuous when the input file was already filtered;
        # the batch itself must cover the fixed scenario catalog.
        records = _fixture_records()
        retained = [
            record
            for record in records
            if record["result"]["verdict"] == contract.VERDICT_MATCH
        ]
        self.assertTrue(retained and len(retained) < len(records))
        views, errors = hp.build_training_views(retained, source="filtered")
        self.assertTrue(
            any(
                "does not cover the scenario catalog" in error
                and "TRAINING_VIEW_HIDES_FAILURE" in error
                for error in errors
            ),
            errors,
        )

    def test_empty_batch_fails_catalog_authentication(self):
        views, errors = hp.build_training_views([], source="empty")
        self.assertEqual(views, [])
        self.assertTrue(
            any("no records to project" in error for error in errors), errors
        )

    def test_completion_is_rederived_instead_of_copying_summary(self):
        record = copy.deepcopy(_fixture_records()[0])
        record["result"]["summary"] = "fabricated completion"
        view = hp.training_view(record)
        self.assertNotEqual(view["completion"], "fabricated completion")

    def test_every_hardware_specific_training_field_is_rederived(self):
        record = copy.deepcopy(_fixture_records()[0])
        mutations = {
            "prompt": "fabricated prompt",
            "completion": "hardware and software matched perfectly",
            "stress": "fabricated-stress",
            "scenario_id": "fabricated-scenario",
        }
        for key, value in mutations.items():
            with self.subTest(key=key):
                view = hp.training_view(record)
                view[key] = value
                errors = hp.training_view_errors(record, view, WHERE)
                self.assertTrue(
                    any(
                        "validator-derived hardware projection" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_swapped_view_ids_are_rejected_against_their_source_records(self):
        records = copy.deepcopy(_fixture_records()[:2])
        views = [hp.training_view(record) for record in records]
        views[0]["id"], views[1]["id"] = views[1]["id"], views[0]["id"]
        errors = []
        for index, (record, view) in enumerate(zip(records, views, strict=True), 1):
            errors += hp.training_view_errors(record, view, f"view:{index}")
        errors += contract.view_set_errors(records, views)
        self.assertTrue(
            any("view id must exactly match" in error for error in errors), errors
        )

    def test_unavailable_deployment_prompt_does_not_claim_execution(self):
        adapter = oracle.FpgaHardwareAdapter(env={})
        record = hp.generate_records(
            round_number=1,
            steps=4,
            deployment_adapter=adapter,
            repeats=2,
        )[0]
        prompt = hp.training_view(record)["prompt"]
        self.assertIn("did not execute", prompt)
        self.assertNotIn("executed on the deployment target", prompt)


if __name__ == "__main__":
    unittest.main()
