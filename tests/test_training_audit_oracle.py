"""Oracle training audit admission and export boundaries."""

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from training_audit_test_helpers import REPO, write
sys.path.insert(0, str(REPO / "pipelines"))
from oracle_grounded import record as oracle_record
import training_audit


def oracle_record_for(family="temporal-memory-spike-challenges", index=0):
    """One genuine reference-simulator oracle record in the committed shape."""
    return json.loads(
        json.dumps(
            oracle_record.build_record(
                family, index, 7, run=oracle_record.RecordRunContext()
            )
        )
    )



class OracleAuditTests(unittest.TestCase):
    def test_oracle_records_are_revalidated_not_counted_blind(self):
        """A rejected oracle row is evidence, not an eligible training record.

        The audit recomputes eligibility from the measured content instead of
        counting every structurally valid oracle line, so an honestly rejected
        record lands in evidence_only_records rather than eligible_records.
        """
        accepted = oracle_record_for(index=0)
        rejected = oracle_record_for(index=5)
        self.assertEqual(rejected["validation"]["status"], "rejected")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "oracle-grounded"
            write(
                root / "temporal-memory-spike-challenges" / "accepted-r01.jsonl",
                [accepted],
            )
            write(
                root / "temporal-memory-spike-challenges" / "rejected-r01.jsonl",
                [rejected],
            )
            report = training_audit.audit_run(root)

        self.assertEqual(report["oracle"]["validation_scope"], "reference_replay_runtime_receipt_required")
        self.assertEqual(report["oracle"]["records"], 2)
        self.assertEqual(report["oracle"]["eligible_records"], 1)
        self.assertEqual(report["oracle"]["evidence_only_records"], 1)
        self.assertEqual(report["oracle"]["invalid_records"], 0)
        self.assertTrue(report["oracle"]["ineligibility_reasons"], report["oracle"])
        self.assertEqual(report["identity"]["top_level_id_records"], 2)
        self.assertEqual(report["identity"]["coverage_pct"], 100.0)

    def test_evidence_only_oracle_record_blocks_the_export(self):
        """A retained-but-ineligible oracle row must not be published.

        The exporter copies every curated row without filtering, so an
        evidence-only record would otherwise reach the train/eval splits.
        """
        accepted = oracle_record_for(index=0)
        rejected = oracle_record_for(index=5)
        self.assertEqual(rejected["validation"]["status"], "rejected")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "oracle-grounded"
            write(
                root / "temporal-memory-spike-challenges" / "accepted-r01.jsonl",
                [accepted],
            )
            write(
                root / "temporal-memory-spike-challenges" / "rejected-r01.jsonl",
                [rejected],
            )
            report = training_audit.audit_run(root)

        self.assertEqual(report["oracle"]["eligible_records"], 1)
        self.assertEqual(report["oracle"]["evidence_only_records"], 1)
        self.assertFalse(report["training_ready"])
        self.assertIn(
            "oracle records are ineligible and must not be exported",
            report["blockers"],
        )

    def test_tampered_oracle_result_blocks_the_audit(self):
        """Editing the measured result while keeping the accepted stamp fails closed."""
        tampered = oracle_record_for(index=0)
        tampered["result"]["measured"]["injected"] = 1.0
        self.assertEqual(tampered["validation"]["status"], "accepted")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "oracle-grounded"
            write(root / "temporal-memory-spike-challenges" / "accepted-r01.jsonl", [tampered])
            report = training_audit.audit_run(root)

        self.assertFalse(report["training_ready"])
        self.assertEqual(report["oracle"]["invalid_records"], 1)
        self.assertIn(
            "oracle records failed validation and are not admissible",
            report["blockers"],
        )

    def test_oracle_shaped_record_under_a_foreign_factory_is_refused(self):
        """An oracle-schema record is oracle-routed wherever it lands, then refused.

        Routing keys on the payload's own schema, not on registry authority:
        if it were registry-gated, a schema-matching record under a factory
        that does not authorize oracle would fall through to the generic path
        and be counted eligible before any oracle invariant ran.
        """
        record = oracle_record_for(index=0)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "run"
            write(root / "thalamic" / "batch-r01.jsonl", [record])
            report = training_audit.audit_run(root)

        self.assertEqual(report["oracle"]["records"], 1)
        self.assertEqual(report["oracle"]["eligible_records"], 0)
        self.assertEqual(report["oracle"]["invalid_records"], 1)
        self.assertEqual(report["totals"]["eligible_records"], 0)
        self.assertFalse(report["training_ready"])
        self.assertIn(
            "oracle records failed validation and are not admissible",
            report["blockers"],
        )


if __name__ == "__main__":
    unittest.main()
