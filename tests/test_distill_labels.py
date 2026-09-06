#!/usr/bin/env python3
"""Direct tests of the family-owned oracle-label policies and the leak check
(``distill_labels``, decision D2)."""

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the shared test support, by bare name

from distill_contract_test_support import (  # noqa: E402
    ENERGY_LABELS,
    FAULT_LABELS,
    minimal_record,
    oc,
)


class FamilyOracleLabels(unittest.TestCase):
    """D2: family-owned oracle-label declarations, never taken from the record."""

    FAULT = "neuromorphic-fault-recovery"
    ENERGY = "snn-energy-routing-preferences"

    def setUp(self):
        from oracle_grounded import distill_labels

        self.labels = distill_labels
        patcher = mock.patch.dict(distill_labels._POLICIES, {}, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def leak_findings(self, errors):
        return [e for e in errors if oc.LABEL_IN_GENERATOR_NAMESPACE in e]

    def test_a_missing_family_policy_is_a_finding_not_a_skip(self):
        record = minimal_record()
        errors = oc.check_oracle_label_leak(record, "x")
        self.assertEqual(len(errors), 1, errors)
        self.assertIn(oc.POLICY_MISSING, errors[0])
        # Structural validation is unchanged by the missing policy, and the
        # finding still refuses curation through the caller's own findings.
        self.assertFalse(any(oc.POLICY_MISSING in e for e in oc.check_envelope(record, "x")))
        eligible, reasons = oc.curation_eligible(record, errors)
        self.assertFalse(eligible)
        self.assertIn("VALIDATION_FINDINGS:1", reasons)

    def test_declarations_are_trusted_code_never_record_content(self):
        record = minimal_record()
        record["scenario"]["trace_summary"] = {"ticks": 3}
        # A record cannot supply its own policy: neither an empty declaration
        # nor a wider one inside the record changes what is checked.
        record["oracle"]["label_keys"] = []
        record["scenario"]["oracle_label_keys"] = []
        record["oracle_label_policy"] = {"family": self.FAULT, "label_keys": []}
        self.assertIn(oc.POLICY_MISSING, oc.check_oracle_label_leak(record, "x")[0])
        oc.declare_oracle_labels(self.FAULT, FAULT_LABELS)
        errors = oc.check_oracle_label_leak(record, "x")
        self.assertEqual(len(self.leak_findings(errors)), 1, errors)
        self.assertIn("scenario.trace_summary", errors[0])

    def test_labels_are_refused_at_any_depth_in_dicts_and_lists(self):
        policy = oc.OracleLabelPolicy(self.ENERGY, ENERGY_LABELS)
        record = minimal_record(family=self.ENERGY)
        record["scenario"]["nested"] = {"deeper": {"preferred": "analytic_kkt"}}
        record["scenario"]["candidate_actions"] = [{"id": "a"}, {"id": "b", "preferred": True}]
        record["intervention"]["steps"] = [[{"cost_value": 2.81e-06}]]
        errors = oc.check_oracle_label_leak(record, "x", policy=policy)
        self.assertEqual(len(errors), 1, errors)
        for path in (
            "scenario.nested.deeper.preferred",
            "scenario.candidate_actions[1].preferred",
            "intervention.steps[0][0].cost_value",
        ):
            with self.subTest(path=path):
                self.assertIn(path, errors[0])

    def test_every_generator_owned_section_is_scanned(self):
        policy = oc.OracleLabelPolicy(self.FAULT, FAULT_LABELS)
        for section in oc.GENERATOR_SECTIONS:
            with self.subTest(section=section):
                record = minimal_record()
                record[section]["max_staleness_ms"] = 12.0
                errors = oc.check_oracle_label_leak(record, "x", policy=policy)
                self.assertEqual(len(errors), 1, errors)
                self.assertIn(f"{section}.max_staleness_ms", errors[0])
        clean = oc.check_oracle_label_leak(minimal_record(), "x", policy=policy)
        self.assertEqual(clean, [])

    def test_valid_prediction_fields_are_not_labels(self):
        # `outcome` is the fault oracle's verdict; `predicted_outcome` and
        # `confidence` are the generator's namespaced guess and stay legal.
        policy = oc.OracleLabelPolicy(self.FAULT, frozenset({"outcome", "reason_codes"}))
        record = minimal_record()
        record["candidate_prediction"] = {"predicted_outcome": "fallback", "confidence": 0.5}
        self.assertEqual(oc.check_oracle_label_leak(record, "x", policy=policy), [])
        record["candidate_prediction"]["outcome"] = "fallback"
        errors = oc.check_oracle_label_leak(record, "x", policy=policy)
        self.assertIn("candidate_prediction.outcome", errors[0])
        self.assertNotIn("predicted_outcome", errors[0])

    def test_an_explicit_policy_must_be_the_records_family(self):
        energy = oc.OracleLabelPolicy(self.ENERGY, ENERGY_LABELS)
        errors = oc.check_oracle_label_leak(minimal_record(), "x", policy=energy)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn(oc.POLICY_MISMATCH, errors[0])

    def test_the_declaration_api_refuses_bad_declarations(self):
        with self.assertRaises(oc.ContractError):
            oc.declare_oracle_labels("no-such-family", {"x"})
        with self.assertRaises(oc.ContractError):
            oc.declare_oracle_labels(self.FAULT, ())
        with self.assertRaises(oc.ContractError):
            oc.declare_oracle_labels(self.FAULT, {"trace_summary", ""})
        first = oc.declare_oracle_labels(self.FAULT, FAULT_LABELS)
        self.assertEqual(oc.declare_oracle_labels(self.FAULT, sorted(FAULT_LABELS)), first)
        with self.assertRaises(oc.ContractError):
            oc.declare_oracle_labels(self.FAULT, FAULT_LABELS | {"outcome"})
        self.assertEqual(oc.declared_families(), (self.FAULT,))
        self.assertIs(oc.oracle_label_policy(self.FAULT), first)
        self.assertIsNone(oc.oracle_label_policy(self.ENERGY))
        self.assertIsNone(oc.oracle_label_policy(None))

    def test_the_review_reproducers_are_caught(self):
        # ORACLE-LABEL-LEAK-SCENARIO: the energy verdict copied into the
        # student-visible scenario, and the fault trace into the scenario.
        oc.declare_oracle_labels(self.ENERGY, ENERGY_LABELS)
        oc.declare_oracle_labels(self.FAULT, FAULT_LABELS)
        energy = minimal_record(family=self.ENERGY)
        energy["scenario"]["preferred"] = "analytic_kkt"
        energy["scenario"]["cost_value"] = 2.81e-06
        energy["scenario"]["decision_rule"] = "cheapest_feasible"
        energy["generator"]["preferred"] = "analytic_kkt"
        errors = oc.check_oracle_label_leak(energy, "x")
        self.assertEqual(len(errors), 1, errors)
        for path in ("scenario.preferred", "scenario.cost_value", "scenario.decision_rule",
                     "generator.preferred"):
            self.assertIn(path, errors[0])
        fault = minimal_record()
        fault["scenario"]["trace_summary"] = {"max_staleness_ms": 40}
        errors = oc.check_oracle_label_leak(fault, "x")
        self.assertIn("scenario.trace_summary", errors[0])
        self.assertIn("scenario.trace_summary.max_staleness_ms", errors[0])

    def test_the_scan_is_the_envelopes_bounded_walker(self):
        policy = oc.OracleLabelPolicy(self.FAULT, FAULT_LABELS)
        record = minimal_record()
        record["scenario"]["junk"] = [{"saturated_ticks": index} for index in range(10_000)]
        errors = oc.check_oracle_label_leak(record, "x", policy=policy)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("scan capped", errors[0])
        self.assertLess(len(errors[0]), 4_000)

    def test_structural_validation_stays_distinct_from_the_family_check(self):
        oc.declare_oracle_labels(self.FAULT, FAULT_LABELS)
        record = minimal_record()
        record["scenario"]["saturated_ticks"] = 4
        record["provenance"]["record_sha256"] = oc.record_digest(record)
        # The structural checks know nothing about the family's labels ...
        self.assertEqual(oc.check_envelope(record, "x"), [])
        # ... the family check refuses the leak, and curation only ever sees
        # it through the findings the composing validator hands over.
        leak = oc.check_oracle_label_leak(record, "x")
        self.assertEqual(len(self.leak_findings(leak)), 1, leak)
        self.assertTrue(oc.curation_eligible(record, [])[0])
        self.assertFalse(oc.curation_eligible(record, leak)[0])



class LabelCheckShape(unittest.TestCase):
    def test_a_non_object_record_is_one_finding(self):
        policy = oc.OracleLabelPolicy("neuromorphic-fault-recovery", FAULT_LABELS)
        for record in ("nope", None, []):
            with self.subTest(record=record):
                self.assertEqual(
                    oc.check_oracle_label_leak(record, "x", policy=policy), ["x: record must be an object"]
                )


if __name__ == "__main__":
    unittest.main()
