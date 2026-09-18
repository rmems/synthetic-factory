"""Training admission needs reproduced measurements and unique identities."""

from pathlib import Path
import re
import sys
from types import SimpleNamespace
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

import curate_identity
import curate_identity_output
from oracle_grounded import admission, canon, families, record
from test_oracle_grounded_record import (
    build, relabel_as_named_runtime, relabel_plasticity_stage_as_named,
)


class OracleTrainingIntegrityTests(unittest.TestCase):
    def _row(self):
        return curate_identity.default_registry().by_path_id["oracle-grounded"]

    def test_current_reference_measurement_remains_eligible(self):
        item = build(families.ENCODER_FAMILY)
        with mock.patch.object(record, "reproduce", wraps=record.reproduce) as replay:
            self.assertEqual(admission.natural_eligibility(item, self._row()), (True, ()))
        self.assertTrue(replay.call_args_list)
        self.assertTrue(all(call == mock.call(item, environ={}) for call in replay.call_args_list))

    def test_recomputed_hash_cannot_authenticate_an_invented_measurement_label(self):
        for family in (families.NEURON_FAMILY, families.MESH_FAMILY):
            with self.subTest(family=family):
                item = build(family)
                item["result"]["measured"]["delta"]["external_attestation"] = "invented"
                item["result_hash"] = canon.digest(item["result"])
                with self.assertRaises(admission.OracleAdmissionError):
                    admission.natural_eligibility(item, self._row())
                item["validation"] = record.assess(item)
                self.assertEqual(item["validation"]["status"], "rejected")
                eligible, reasons = admission.natural_eligibility(item, self._row())
                self.assertFalse(eligible)
                self.assertTrue(reasons)

    def test_runtime_measurements_require_authenticated_replay_without_implicit_execution(self):
        reference = build(families.CREDIT_FAMILY)
        for item in (relabel_as_named_runtime(reference), relabel_plasticity_stage_as_named(reference)):
            with self.subTest(implementation=item["oracle"]["implementation"]):
                self.assertEqual(record.validate_record(item), [])
                with mock.patch.object(record, "reproduce") as replay:
                    eligible, reasons = admission.natural_eligibility(item, self._row())
                self.assertFalse(eligible)
                self.assertIn("authenticated runtime replay required", reasons)
                replay.assert_not_called()

    def test_preserved_oracle_ids_are_unique_across_source_coordinates(self):
        mapping = {
            "record_kind": "oracle", "output_id": "oracle-example",
            "output_sha256": "0" * 64, "registry": {"sha256": "registry-pin"},
        }
        retained = SimpleNamespace(action="retained", mapping=mapping)
        replays = [SimpleNamespace(
            source=SimpleNamespace(path="oracle/source.jsonl", line=line), result=retained,
        ) for line in (1, 2)]
        dependencies = SimpleNamespace(
            identity_tree_error=ValueError, sha256_pattern=re.compile(r"[0-9a-f]{64}"),
            replay_manifest_mapping=mock.Mock(side_effect=replays),
        )
        with self.assertRaisesRegex(ValueError, "duplicate preserved oracle ID"):
            curate_identity_output.expected_identity_outputs(
                [mapping, mapping], SimpleNamespace(sha256="registry-pin"), dependencies,
            )

    def test_untrusted_neuron_trace_is_bounded_before_per_sample_findings(self):
        item = build(families.NEURON_FAMILY)
        item["oracle"]["implementation"] = "named-runtime"
        item["result"]["measured"]["before"]["v_trace"] = [-1000000] * 1000
        findings = families._neuron_checks(item)
        self.assertLess(len(findings), 100)
        self.assertTrue(any("v_trace length" in finding for finding in findings), findings)


if __name__ == "__main__":
    unittest.main()
