"""Explicit assembly selection keeps rejected source evidence replayable."""

import contextlib
import io
import hashlib
import os
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pipelines'))
import compose_curated
import compose_oracle_selection
import export_hf
import oracle_generate
from oracle_grounded import oracles, record as oracle_record
from export_contract import ExportError


class OracleTrainingSelection(unittest.TestCase):
    def _generate(self, source, dirty=False):
        commit = oracles.resolve_commit()[0]
        # Explicit test-only provenance fixture; CLI checkout checks have separate tests.
        with mock.patch.object(oracle_generate, '_resolve_stamp', return_value=(commit, dirty, None)):
            with mock.patch.dict(os.environ, {}, clear=True), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(oracle_generate.main(['--count', '7', '--seed', '20260918', str(source)]), 0)

    def _compose(self, root):
        self._generate(root / 'source')
        return compose_curated.compose_run(root / 'source', root / 'curated', oracle_selection='eligible-training')

    def _rewrite_summary(self, curated, summary):
        (curated / 'COMPOSE.json').write_text(json.dumps(summary))

    def test_fresh_mixed_run_selects_eligible_records_and_exports_exact_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, curated, exported = root / 'source', root / 'curated', root / 'export'
            self._generate(source)
            before = {p.relative_to(source): p.read_bytes() for p in source.rglob('*') if p.is_file()}
            summary = compose_curated.compose_run(source, curated, oracle_selection='eligible-training')
            self.assertEqual(summary['counts']['source_records'], 35)
            self.assertEqual(summary['counts']['retained'], 34)
            self.assertEqual(summary['counts']['excluded'], 1)
            self.assertTrue(summary['audit']['training_ready'])
            entries = [json.loads(line) for line in (curated / 'manifest/compose-manifest.jsonl').read_text().splitlines()]
            self.assertEqual(len(entries), 35)
            for entry in entries:
                original = before[Path(entry['physical_source_path'])].split(b'\n')[entry['source_line'] - 1]
                self.assertEqual(entry['source_original'].encode(), original)
                self.assertEqual(entry['stages'][-1]['lane'], 'selection')
                if entry['action'] == 'retained':
                    emitted = (curated / entry['output_path']).read_bytes().split(b'\n')[entry['output_line'] - 1]
                    self.assertEqual(emitted, original)
                else:
                    self.assertIn('compose.oracle_training_ineligible', entry['reason_codes'])
                    self.assertIsNone(entry['output_path'])
            result = export_hf.export_run(curated, exported)
            self.assertEqual(result['records'], 34)
            self.assertEqual(result['compose']['oracle_selection'], summary['oracle_selection'])
            self.assertEqual(before, {p.relative_to(source): p.read_bytes() for p in source.rglob('*') if p.is_file()})

    def test_unfiltered_or_all_ineligible_corpora_remain_unexportable(self):
        cases = ((False, 'all', 35), (None, 'eligible-training', 0))
        for dirty, mode, retained in cases:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self._generate(root / 'source', dirty=dirty)
                summary = compose_curated.compose_run(root / 'source', root / 'curated', oracle_selection=mode)
                self.assertEqual('oracle_selection' in summary, mode != 'all')
                self.assertEqual(summary['counts']['retained'], retained)
                self.assertEqual(summary['counts']['excluded'], 35 - retained)
                self.assertFalse(summary['audit']['training_ready'])
                with self.assertRaises(ExportError):
                    export_hf.export_run(root / 'curated', root / 'export')

    def test_selection_declaration_must_match_manifest_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary = self._compose(root)
            descriptor = summary['oracle_selection']
            variants = [None, {'mode': 'all'}, {**descriptor, 'version': True},
                        {**descriptor, 'extra': 1}, {**descriptor, 'mode': 'unknown'}]
            for variant in variants:
                with self.subTest(variant=variant):
                    altered = dict(summary)
                    if variant is None:
                        del altered['oracle_selection']
                    else:
                        altered['oracle_selection'] = variant
                    self._rewrite_summary(root / 'curated', altered)
                    with self.assertRaises(ExportError):
                        export_hf.export_run(root / 'curated', root / 'export')
                    self.assertFalse((root / 'export').exists())

    def test_forged_exclusion_reason_cannot_be_authenticated_by_rehashing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary = self._compose(root)
            manifest = root / 'curated' / summary['manifest']['path']
            entries = [json.loads(line) for line in manifest.read_text().splitlines()]
            excluded = next(entry for entry in entries if entry['action'] == 'excluded')
            excluded['stages'][-1]['detail']['ineligibility_reasons'] = ['invented reason']
            manifest.write_text(''.join(json.dumps(entry) + '\n' for entry in entries))
            summary['manifest']['sha256'] = hashlib.sha256(manifest.read_bytes()).hexdigest()
            self._rewrite_summary(root / 'curated', summary)
            with self.assertRaisesRegex(ExportError, 'does not reproduce'):
                export_hf.export_run(root / 'curated', root / 'export')

    def test_invalid_selected_out_source_is_fatal_even_with_refreshed_file_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'source'
            self._generate(source)
            manifest_path = source / 'manifest.json'
            manifest = json.loads(manifest_path.read_text())
            relative = 'temporal-memory-spike-challenges/rejected-r01.jsonl'
            path = source / relative
            record = json.loads(path.read_text())
            record['result']['measured']['counterfeit'] = True
            record['validation']['publishable'] = True
            path.write_text(json.dumps(record) + '\n')
            manifest['files'][relative]['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaises(compose_curated.ComposeError):
                compose_curated.compose_run(source, root / 'curated', oracle_selection='eligible-training')
            self.assertFalse((root / 'curated').exists())

    def test_empty_manifest_member_cannot_be_omitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._generate(root / 'source')
            empty = next(path for path in (root / 'source').rglob('*.jsonl') if not path.read_bytes())
            empty.unlink()
            with self.assertRaises(compose_curated.ComposeError):
                compose_curated.compose_run(root / 'source', root / 'curated', oracle_selection='eligible-training')
            self.assertFalse((root / 'curated').exists())

    def test_selection_requires_whole_authenticated_oracle_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._generate(root / 'source')
            (root / 'source' / 'manifest.json').unlink()
            with self.assertRaisesRegex(compose_curated.ComposeError, 'complete authenticated oracle run'):
                compose_curated.compose_run(root / 'source', root / 'curated', oracle_selection='eligible-training')
            self.assertFalse((root / 'curated').exists())

    def test_named_and_mixed_records_are_excluded_without_implicit_runtime_execution(self):
        from test_oracle_grounded_record import build, relabel_as_named_runtime, relabel_plasticity_stage_as_named
        reference = build('neuromodulator-credit-assignment')
        for record in (relabel_as_named_runtime(reference), relabel_plasticity_stage_as_named(reference)):
            with self.subTest(implementation=record['oracle']['implementation']):
                coordinate = compose_curated.SourceLineCoordinate('oracle-grounded/records.jsonl', 1, 'a' * 64)
                with mock.patch.object(oracle_record, 'reproduce') as replay:
                    fresh = compose_curated.compose_source_line(json.dumps(record).encode(), coordinate)
                    decision = compose_oracle_selection.apply_selection(fresh, 'eligible-training')
                replay.assert_not_called()
                self.assertEqual(decision.action, 'excluded')
                self.assertIn('authenticated runtime replay required', decision.stages[-1]['detail']['ineligibility_reasons'])


if __name__ == '__main__':
    unittest.main()
