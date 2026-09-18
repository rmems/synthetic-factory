"""Fatal oracle errors stop one atomic run without discarding honest verdicts."""

import copy
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))
import oracle_generate
from oracle_grounded import canon, families, oracles, record
from test_oracle_grounded_record import build


class OracleGenerationFailureTests(unittest.TestCase):
    def _generate(self, family=families.ENCODER_FAMILY, count=20):
        return oracle_generate.generate_family(family, count, 7, 1, None, None, False, environ={})

    def test_fatal_build_errors_are_not_retried_for_every_proposal(self):
        for error_type in (oracles.OracleError, record.GenerationError):
            with self.subTest(error=error_type.__name__), mock.patch.object(
                record, "build_record", side_effect=error_type("fatal fixture"),
            ) as builder:
                accepted, rejected, errors = self._generate()
                self.assertEqual((accepted, rejected), ([], []))
                self.assertEqual(len(errors), 1)
                builder.assert_called_once()

    def test_corrupt_generated_envelopes_abort_remaining_proposals(self):
        item = build(families.ENCODER_FAMILY)
        item["schema"] = "invalid"
        with mock.patch.object(record, "build_record", return_value=item) as builder:
            accepted, rejected, errors = self._generate()
        self.assertEqual((accepted, rejected), ([], []))
        self.assertEqual(len(errors), 1)
        builder.assert_called_once()

    def test_fatal_family_error_stops_the_unpublishable_atomic_run(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "run"
            with (
                mock.patch.object(oracle_generate, "generate_family", return_value=([], [], ["fatal fixture"])) as generate,
                mock.patch.object(sys, "stderr", io.StringIO()) as errors,
            ):
                status = oracle_generate.main([
                    "--family", families.ENCODER_FAMILY,
                    "--family", families.NEURON_FAMILY, str(out),
                ])
            self.assertEqual(status, 1)
            self.assertIn("fatal fixture", errors.getvalue())
            generate.assert_called_once()
            self.assertFalse(out.exists())

    def test_honest_family_rejections_do_not_stop_generation(self):
        item = build(families.MEMORY_FAMILY)
        measured = item["result"]["measured"]
        measured["probes"] = {name: copy.deepcopy(measured["baseline"]) for name in measured["probes"]}
        item["result_hash"] = canon.digest(item["result"])
        item["validation"] = record.assess(item)
        self.assertEqual(item["validation"]["status"], "rejected")
        with mock.patch.object(record, "build_record", return_value=item) as builder:
            accepted, rejected, errors = self._generate(families.MEMORY_FAMILY, 3)
        self.assertEqual(accepted, [])
        self.assertEqual(len(rejected), 3)
        self.assertEqual(errors, [])
        self.assertEqual(builder.call_count, 3)


if __name__ == "__main__":
    unittest.main()
