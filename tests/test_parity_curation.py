"""Fresh native parity observations retain their research-only source identity."""

import json
from pathlib import Path
import tempfile
import unittest

from pipelines import check_records, curate_identity, hardware_parity, nir_equivalence, training_audit


def fresh_parity_records():
    return tuple(record for producer in (hardware_parity, nir_equivalence)
                 for record in producer.generate_records(round_number=37, steps=16))


def write_parity_records(root, records):
    for factory in {record['meta']['factory'] for record in records}:
        path = root / factory / 'fresh.jsonl'
        path.parent.mkdir(parents=True)
        path.write_text(''.join(json.dumps(record) + '\n' for record in records
                                if record['meta']['factory'] == factory))


class FreshParityCuration(unittest.TestCase):
    def test_fresh_producers_retain_original_native_envelopes(self):
        for record in fresh_parity_records():
            with self.subTest(record=record['id']):
                self.assertEqual(check_records.check_record(record, 'fresh')[0], [])
                source = curate_identity.SourceRecord(record, record['meta']['factory'] + '/fresh.jsonl', 1)
                result = curate_identity.curate_record(source)
                self.assertEqual(result.action, 'retained', result.mapping.get('details'))
                self.assertEqual(result.record, record)

    def test_fresh_complete_corpus_is_always_research_only(self):
        records = fresh_parity_records()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_parity_records(root, records)
            report = training_audit.audit_run(root)
        self.assertEqual(report['totals']['records'], 15)
        self.assertEqual(report['totals']['eligible_records'], 0)
        self.assertEqual(report['identity']['coverage_pct'], 100.0)
        self.assertFalse(report['training_ready'])
        self.assertTrue(any('research-only' in reason for reason in report['blockers']))


class ParityDatasetAssembly(unittest.TestCase):
    def test_actual_composition_preserves_native_bytes_and_refuses_training_export(self):
        from pipelines import compose_curated, export_hf
        records = fresh_parity_records()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'source'
            write_parity_records(source, records)
            composed = root / 'composed'
            summary = compose_curated.compose_run(compose_curated.ComposeRunContext(source, composed))
            self.assertEqual(summary['counts']['retained'], 15)
            for original in source.glob('*/*.jsonl'):
                output = composed / 'records' / original.relative_to(source)
                self.assertEqual(output.read_bytes(), original.read_bytes())
            files, _rows, _snapshot = export_hf._curated_snapshot(composed / 'records')
            report = training_audit.audit_run(composed / 'records')
            self.assertEqual(report['totals']['eligible_records'], 0)
            self.assertTrue(export_hf._compose_metadata(composed, files, report))
            with self.assertRaisesRegex(export_hf.ExportError, 'research-only'):
                export_hf.export_run(export_hf.ExportRequest(composed, root / 'training-export'))
            self.assertFalse((root / 'training-export').exists())

    def test_identity_tree_replays_native_bytes_and_rejects_manifest_authority_change(self):
        records = fresh_parity_records()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, target = root / 'source', root / 'identity'
            write_parity_records(source, records)
            curate_identity.write_run(source, target)
            curate_identity.validate_identity_tree(target)
            for original in source.glob('*/*.jsonl'):
                self.assertEqual((target / original.relative_to(source)).read_bytes(), original.read_bytes())
            manifest = target / 'IDENTITY-MANIFEST.json'
            entries = json.loads(manifest.read_text())
            entries[0]['parity_authority']['project_training_policy'] = 'allowed'
            manifest.write_text(json.dumps(entries))
            with self.assertRaises(curate_identity.IdentityTreeError):
                curate_identity.validate_identity_tree(target)
