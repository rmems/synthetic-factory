"""Research authorship remains blocked in malformed and mixed parity corpora."""
import copy
from pathlib import Path
import tempfile
import unittest

from pipelines import curate_identity as identity, training_audit, export_hf
from tests.test_parity_curation import fresh_parity_records, write_parity_records
from tests.training_audit_test_helpers import thalamic, write


class ParityTrainingPolicy(unittest.TestCase):
    def test_source_and_authorship_mutations_never_retain_or_become_eligible(self):
        for original in fresh_parity_records()[::6]:
            cases = []
            for field in ('generator_version', 'catalog_digest', 'catalog_authorship'):
                changed = copy.deepcopy(original)
                del changed['provenance'][field]
                cases.append(changed)
            changed = copy.deepcopy(original)
            changed['unreviewed'] = {'nested': [{'training_ready': True}]}
            cases.append(changed)
            changed = copy.deepcopy(original)
            changed['result']['verdict'] = 'fabricated'
            cases.append(changed)
            for index, changed in enumerate(cases):
                with self.subTest(record=original['id'], case=index), tempfile.TemporaryDirectory() as temporary:
                    path = changed['meta']['factory'] + '/fresh.jsonl'
                    result = identity.curate_record(identity.SourceRecord(changed, path, 1))
                    self.assertEqual(result.action, 'exclude')
                    root = Path(temporary)
                    write_parity_records(root, [changed])
                    report = training_audit.audit_run(root)
                    self.assertEqual(report['totals']['eligible_records'], 0)
                    self.assertFalse(report['training_ready'])
                    self.assertEqual(report['totals']['invalid_parity_records'], 1)

    def test_parity_record_in_mixed_ready_corpus_keeps_export_blocked(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            curated = root / 'curated'
            records = curated / 'records'
            write(records / 'other' / 'ready.jsonl', [thalamic('ordinary-1')])
            baseline = training_audit.audit_run(records)
            self.assertTrue(baseline['training_ready'], baseline['blockers'])
            write_parity_records(records, [fresh_parity_records()[0]])
            report = training_audit.audit_run(records)
            self.assertEqual(report['totals']['eligible_records'], 1)
            self.assertEqual(report['identity']['coverage_pct'], 100.0)
            self.assertFalse(report['training_ready'])
            self.assertTrue(any('research-only' in reason for reason in report['blockers']))
            with self.assertRaisesRegex(export_hf.ExportError, 'research-only'):
                export_hf.export_run(curated, root / 'export')
            self.assertFalse((root / 'export').exists())

    def test_wrong_source_directory_has_no_native_authority(self):
        record = fresh_parity_records()[0]
        result = identity.curate_record(identity.SourceRecord(record, 'thalamic-trajectory-factory/fresh.jsonl', 1))
        self.assertEqual(result.action, 'exclude')

    def test_duplicate_native_ids_are_rejected_before_identity_publication(self):
        record = fresh_parity_records()[0]
        factory = record['meta']['factory']
        sources = [identity.SourceRecord(record, factory + '/' + name, 1)
                   for name in ('first.jsonl', 'second.jsonl')]
        with self.assertRaises(identity.CanonicalIdCollision):
            identity.curate_records(sources)

    def test_altered_actual_oracle_value_fails_admission_and_manifest_replay(self):
        record = fresh_parity_records()[0]
        changed = copy.deepcopy(record)
        changed['oracle']['software']['membrane']['trace'][0][0] = 99
        result = identity.curate_record(identity.SourceRecord(changed, record['meta']['factory'] + '/fresh.jsonl', 1))
        self.assertEqual(result.action, 'exclude')
        from pipelines import curate_gate_manifests, curate_parity
        original = identity.curate_record(identity.SourceRecord(record, record['meta']['factory'] + '/fresh.jsonl', 1))
        entry = curate_gate_manifests._normalize_entry(original.mapping, {
            'order': 1, 'transform': 'curate_identity', 'version': identity.TRANSFORM_VERSION})
        with self.assertRaises(curate_parity.GateError):
            curate_parity.authenticate(entry, changed, 'changed oracle')
