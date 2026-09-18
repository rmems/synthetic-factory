"""Parity projections retain catalog policy and deterministic reference probes."""

import copy
import os
import unittest
from unittest.mock import patch

import hardware_parity as hp
import nir_equivalence as nir
from parity_contract_support import contract, make_record, make_view


class CatalogPolicyViews(unittest.TestCase):
    def test_views_retain_independent_catalog_provenance_copies(self):
        for module in (hp, nir):
            record = module.generate_records()[0]
            view = module.training_view(record)
            with self.subTest(module=module.__name__):
                self.assertEqual(view.get("provenance"), record["provenance"])
                authorship = view["provenance"]["catalog_authorship"]
                self.assertEqual(authorship["project_training_policy"], "blocked")
                self.assertEqual(authorship["intended_use"], "research_only")
                original = copy.deepcopy(record)
                authorship["project_training_policy"] = "allowed"
                self.assertEqual(record, original)
                self.assertTrue(module.training_view_errors(record, view, "view"))

    def test_reference_defaults_ignore_ambient_fpga_configuration(self):
        baseline = hp.generate_records()
        with patch.dict(os.environ, {"SPIKENAUT_FPGA_DEVICE": "/definitely/missing"}):
            self.assertEqual(hp.generate_records(), baseline)

    def test_explicit_environment_still_records_operator_selected_probe(self):
        records = hp.generate_records(env={"SPIKENAUT_FPGA_DEVICE": "/definitely/missing"})
        self.assertEqual(records[0]["oracle"]["environment"]["fpga_hardware"]["reason_code"], "FPGA_DEVICE_ABSENT")


class MalformedViewInputs(unittest.TestCase):
    def test_non_string_verdicts_report_refusal_without_hashing(self):
        for verdict in ([], {}):
            with self.subTest(verdict=verdict):
                record = make_record()
                record["result"]["verdict"] = verdict
                view = make_view(record)
                self.assertTrue(contract.training_view_errors(record, view, "view"))

    def test_non_object_record_and_view_sets_are_reported(self):
        for records, views in (([None], []), ([], [[]]), (["record"], [{}])):
            with self.subTest(records=records, views=views):
                self.assertTrue(contract.view_set_errors(records, views))

    def test_unhashable_catalog_coordinates_are_reported(self):
        for section, key in (("meta", "round"), ("scenario", "id")):
            for value in ([], {}, True):
                record = make_record()
                record[section][key] = value
                with self.subTest(section=section, value=value):
                    self.assertTrue(contract.catalog_batch_errors([record], ["sc-001"]))
