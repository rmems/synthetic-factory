"""Training admission needs reproduced measurements and unique identities."""

from contextlib import ExitStack
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


def _record_twins():
    """Both import spellings of the record module; ``record.py`` binds no twin."""
    twins = (sys.modules.get(name) for name in ("oracle_grounded.record", "pipelines.oracle_grounded.record"))
    return list({id(module): module for module in twins if module is not None}.values())


class OracleTrainingIntegrityTests(unittest.TestCase):
    def _row(self):
        return curate_identity.default_registry().by_path_id["oracle-grounded"]

    def _patch_reproduce(self, stack, **kwargs):
        replay = mock.Mock(**kwargs)
        for module in _record_twins():
            stack.enter_context(mock.patch.object(module, "reproduce", replay))
        return replay

    def test_current_reference_measurement_remains_eligible(self):
        item = build(families.ENCODER_FAMILY)
        with ExitStack() as stack:
            replay = self._patch_reproduce(stack, wraps=record.reproduce)
            self.assertEqual(admission.natural_eligibility(item, self._row()), (True, ()))
        replay.assert_called_once_with(item, environ={})

    def test_recomputed_hash_cannot_authenticate_an_invented_measurement_label(self):
        for family in (families.NEURON_FAMILY, families.MESH_FAMILY):
            with self.subTest(family=family):
                item = build(family)
                row = self._row()
                item["result"]["measured"]["delta"]["external_attestation"] = "invented"
                item["result_hash"] = canon.digest(item["result"])
                with self.assertRaises(admission.OracleAdmissionError):
                    admission.natural_eligibility(item, row)
                item["validation"] = record.assess(item)
                self.assertEqual(item["validation"]["status"], "rejected")
                with self.assertRaises(admission.OracleAdmissionError):
                    admission.natural_eligibility(item, row)

    def test_runtime_measurements_require_authenticated_replay_without_implicit_execution(self):
        reference = build(families.CREDIT_FAMILY)
        for item in (relabel_as_named_runtime(reference), relabel_plasticity_stage_as_named(reference)):
            with self.subTest(implementation=item["oracle"]["implementation"]):
                self.assertEqual(record.validate_record(item), [])
                with ExitStack() as stack:
                    replay = self._patch_reproduce(stack)
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
        registry = SimpleNamespace(sha256="registry-pin")
        with self.assertRaisesRegex(ValueError, "duplicate preserved oracle ID"):
            curate_identity_output.expected_identity_outputs(
                [mapping, mapping], registry, dependencies,
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
