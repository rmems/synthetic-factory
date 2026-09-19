"""Batch input refusals and reviewed factory policy cannot grant export authority."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pipelines import curate_identity as identity, training_audit, export_hf
from pipelines import curate_identity_simulator_process as process
from pipelines.oracle_grounded import fault_oracle
from tests.test_curate_identity import episode

STAMP = '2026-08-23T00:00:00.000Z'
FACTORY = 'fault-recovery-simulator-factory'


class SimulatorReviewBoundaries(unittest.TestCase):
    def test_bad_timestamp_does_not_poison_later_batch_records(self):
        records = fault_oracle.build_records(42, 3, produced_at=STAMP)
        records[1]['provenance']['produced_at'] = 'not-a-timestamp'
        sources = [identity.SourceRecord(record, FACTORY + '/records.jsonl', index + 1)
                   for index, record in enumerate(records)]
        with patch.object(process.subprocess, 'Popen', wraps=process.subprocess.Popen) as launch:
            results = identity.curate_records(sources)
        self.assertEqual([result.action for result in results], ['retained', 'exclude', 'retained'])
        self.assertEqual(launch.call_count, 1)

    def test_invalid_timestamp_is_refused_before_any_worker_request(self):
        for stamp in ('bad', '2026-02-30T00:00:00.000Z', ''):
            with self.subTest(stamp=stamp), patch.object(process.subprocess, 'Popen') as launch:
                with self.assertRaises(identity.IdentityCurationError):
                    process.replay_coordinate((42, 0, stamp))
                launch.assert_not_called()

    def test_native_research_record_cannot_borrow_procedural_path_authority(self):
        record = fault_oracle.build_records(42, 1, produced_at=STAMP)[0]
        path = 'python-function-repair-factory/records.jsonl'
        with tempfile.TemporaryDirectory() as temporary:
            report = training_audit.audit_run(Path(temporary), snapshot={
                path: (json.dumps(record) + '\n').encode()})
        self.assertEqual(report['totals']['eligible_records'], 0)
        self.assertFalse(report['training_ready'])
        result = identity.curate_record(identity.SourceRecord(record, path, 1))
        self.assertEqual(result.action, 'exclude')

    def test_procedural_directory_requires_procedural_source_validation(self):
        factory = 'python-function-repair-factory'
        record = episode(factory, id='misfiled-episode', provenance={'kind': 'designed'})
        with tempfile.TemporaryDirectory() as temporary:
            report = training_audit.audit_run(Path(temporary), snapshot={
                factory + '/records.jsonl': (json.dumps(record) + '\n').encode()})
        self.assertEqual(report['totals']['eligible_records'], 0)
        self.assertEqual(report['code_repair']['invalid_records'], 1)
        self.assertGreater(report['record_invariants']['errors'], 0)
        self.assertFalse(report['training_ready'])

    def test_placeholder_episodes_cannot_become_training_ready_or_export(self):
        for factory in ('deepseek-placeholder-factory', 'nemotron-placeholder-factory',
                        'agentic-coding-trajectory-factory'):
            with self.subTest(factory=factory), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                record = episode(factory, id='placeholder-1', provenance={'kind': 'designed'})
                target = root / 'curated' / 'records' / factory / 'episodes.jsonl'
                target.parent.mkdir(parents=True)
                target.write_text(json.dumps(record) + '\n')
                report = training_audit.audit_run(target.parents[1])
                self.assertEqual(report['totals']['eligible_records'], 0)
                self.assertFalse(report['training_ready'])
                with self.assertRaises(export_hf.ExportError):
                    export_hf.export_run(root / 'curated', root / 'export')
                self.assertFalse((root / 'export').exists())


class ReviewedAuditPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tests.code_repair_admission_test_support import build_generated_admission_evidence
        cls.root, _run, cls.records, cls.row = build_generated_admission_evidence(cls)

    def test_mixed_corpus_keeps_procedural_eligibility_but_blocks_export(self):
        from pipelines.code_repair.admission import natural_eligibility
        accepted = next(record for record in self.records
                        if natural_eligibility(record, self.row)[0])
        snapshot = {self.row.path_id + '/records.jsonl': (json.dumps(accepted) + '\n').encode()}
        for factory in ('deepseek-placeholder-factory', 'nemotron-placeholder-factory',
                        'agentic-coding-trajectory-factory'):
            record = episode(factory, id=factory + '-1', provenance={'kind': 'designed'})
            snapshot[factory + '/records.jsonl'] = (json.dumps(record) + '\n').encode()
        report = training_audit.audit_run(self.root, snapshot=snapshot)
        self.assertEqual(report['totals']['eligible_records'], 1)
        self.assertEqual(report['totals']['research_only_records'], 3)
        self.assertEqual(report['identity']['coverage_pct'], 100.0)
        self.assertEqual(report['record_invariants']['errors'], 0)
        self.assertFalse(report['training_ready'])
        self.assertTrue(any('research-only' in reason for reason in report['blockers']))
        with self.assertRaisesRegex(export_hf.ExportError, 'research-only'):
            export_hf._training_ready_audit(self.root, snapshot)

    def test_payload_claims_cannot_override_reviewed_path_policy(self):
        factory = 'deepseek-placeholder-factory'
        for mutation in ('contradictory_factory', 'self_certification'):
            with self.subTest(mutation=mutation):
                record = episode(factory, id='policy-claim', provenance={'kind': 'designed'})
                if mutation == 'contradictory_factory':
                    record['meta']['factory'] = self.row.path_id
                else:
                    record['meta']['training_ready'] = 'yes'
                path = factory + '/records.jsonl'
                report = training_audit.audit_run(self.root, snapshot={
                    path: (json.dumps(record) + '\n').encode()})
                self.assertEqual(report['totals']['eligible_records'], 0)
                self.assertFalse(report['training_ready'])
                result = identity.curate_record(identity.SourceRecord(record, path, 1))
                self.assertEqual(result.action, 'exclude')
