"""The Agoge consumer probe: its text boundary, its refusals and its orchestration."""
import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from scripts import agoge_consumer_probe as probe


class ConsumerBoundary(unittest.TestCase):
    def test_unicode_boundary_ignores_embedded_separator(self):
        validate = getattr(probe, 'completion_boundary', None)
        self.assertTrue(callable(validate), 'explicit boundary validator is missing')
        prompt = 'π inside source' + probe.SEPARATOR + 'more prompt' + probe.SEPARATOR
        row = {'text': prompt + 'def corrected():\n    return "é"\n',
               'completion_start_char': len(prompt)}
        self.assertEqual(validate(row), len(prompt))
        for value in (True, -1, len(row['text']), '12', None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate({**row, 'completion_start_char': value})

    def test_boundary_requires_the_declared_separator_and_a_nonempty_completion(self):
        for row, message in (
            ({'text': 'promptdef corrected():\n    pass\n', 'completion_start_char': 6},
             'does not delimit'),
            ({'text': 'prompt' + probe.SEPARATOR + '   ',
              'completion_start_char': len('prompt' + probe.SEPARATOR)},
             'does not delimit'),
            ({'text': None, 'completion_start_char': 1}, 'invalid completion_start_char'),
        ):
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                probe.completion_boundary(row)


class ConsumerProbeFailures(unittest.TestCase):
    def test_guarded_reports_exceptions_and_never_exposes_internal_records(self):
        visible, records = probe._guarded(
            lambda: {'status': 'loaded', 'records': [{'canonical_id': 'private'}]}
        )
        self.assertEqual(visible, {'status': 'loaded'})
        self.assertEqual(records, [{'canonical_id': 'private'}])

        refused, records = probe._guarded(
            lambda: (_ for _ in ()).throw(ValueError('bad source'))
        )
        self.assertEqual(refused, {'error': 'ValueError: bad source', 'agree': False})
        self.assertEqual(records, [])

    def test_manifest_proof_binds_bytes_row_count_and_completion_boundaries(self):
        row = {
            'canonical_id': 'code-repair:test',
            'text': 'prompt' + probe.SEPARATOR + 'def corrected():\n    return 1\n',
            'completion_start_char': len('prompt' + probe.SEPARATOR),
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'records.jsonl'
            path.write_text(json.dumps(row) + '\n', encoding='utf-8')
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest = {
                'files': {'agoge/code_repair_v1.jsonl': digest},
                'tables': {'dispositions': {'exported': 1}},
            }
            self.assertEqual(probe._manifest_proof(path, manifest, 1),
                             {'sha256': digest, 'rows': 1})

            with self.assertRaisesRegex(ValueError, 'sha256'):
                probe._manifest_proof(
                    path,
                    {**manifest, 'files': {'agoge/code_repair_v1.jsonl': '0' * 64}},
                    1,
                )
            with self.assertRaisesRegex(ValueError, 'row count'):
                probe._manifest_proof(path, manifest, 2)

            row['completion_start_char'] = 1
            path.write_text(json.dumps(row) + '\n', encoding='utf-8')
            manifest['files']['agoge/code_repair_v1.jsonl'] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            with self.assertRaisesRegex(ValueError, 'does not delimit'):
                probe._manifest_proof(path, manifest, 1)

    def test_freeze_requires_real_provenance_before_materialization(self):
        ready = SimpleNamespace(
            freeze_into=Path('snapshot'), agoge_jsonl=Path('records.jsonl'),
            source_revision='a' * 40, dataset_version='v1',
        )
        for revision, version in ((None, 'v1'), ('short', 'v1'), ('0' * 40, 'v1'),
                                  ('a' * 40, None), ('a' * 40, 'probe')):
            args = SimpleNamespace(**{**vars(ready), 'source_revision': revision,
                                      'dataset_version': version})
            with self.subTest(revision=revision, version=version):
                self.assertIs(probe._freeze_ready(args), False)
                report = {}
                probe._freeze_step(report, args, object())
                self.assertEqual(
                    report['freeze']['error'],
                    'freeze requires real --source-revision and --dataset-version',
                )

        self.assertIs(probe._freeze_ready(ready), True)
        report = {}
        with mock.patch.object(probe, '_freeze', return_value={'output_dir': 'snapshot'}):
            probe._freeze_step(report, ready, object())
        self.assertEqual(report['freeze'], {'output_dir': 'snapshot'})
        untouched = {}
        no_destination = SimpleNamespace(**{**vars(ready), 'freeze_into': None})
        probe._freeze_step(untouched, no_destination, object())
        self.assertEqual(untouched, {})

    def test_split_steps_explain_absent_policy_and_spec_refusal(self):
        args = SimpleNamespace(
            freeze_into=Path('snapshot'), source_path='source.jsonl',
            source_revision=None, dataset_version=None,
        )
        report = {'policy': None}
        probe._split_steps(report, [], [], args)
        self.assertEqual(report, {
            'split_agreement': {'status': 'not evaluated: no split policy'},
            'freeze': {'error': 'no split policy'},
        })

        report = {'policy': {'seed': 1, 'salt': 'x', 'weights': {}}}
        with mock.patch.object(probe, '_spec', side_effect=ValueError('bad policy')):
            probe._split_steps(report, [], [], args)
        self.assertEqual(report['split_agreement'], {
            'error': 'ValueError: bad policy', 'agree': False,
        })

    def test_failed_steps_include_required_errors_and_disagreement_once(self):
        args = SimpleNamespace(config=Path('config.yaml'), freeze_into=Path('snapshot'))
        report = {
            'manifest': {}, 'load': {'error': 'load failed'},
            'split_agreement': {'error': 'different split', 'agree': False},
            'labels': {}, 'freeze': {},
        }
        self.assertEqual(probe._failed_steps(report, args), ['load', 'split_agreement'])
        self.assertEqual(probe._failed_steps(
            {'manifest': {}, 'load': {}, 'split_agreement': {'agree': True}},
            SimpleNamespace(config=None, freeze_into=None),
        ), [])

    def test_main_reports_manifest_refusal_in_human_and_json_modes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            records = root / 'records.jsonl'
            records.write_text('{}\n', encoding='utf-8')
            manifest = root / 'MANIFEST.json'
            manifest.write_text(json.dumps({
                'files': {'agoge/code_repair_v1.jsonl': '0' * 64},
                'tables': {'dispositions': {'exported': 1}},
                'run': {'split_policy': None},
            }), encoding='utf-8')
            argv = [str(records), '--manifest', str(manifest)]

            human = io.StringIO()
            with contextlib.redirect_stdout(human):
                self.assertEqual(probe.main(argv), 1)
            self.assertEqual(human.getvalue(), 'passed=False rows=1 failed_steps=manifest\n')

            machine = io.StringIO()
            with contextlib.redirect_stdout(machine):
                self.assertEqual(probe.main(argv + ['--json']), 1)
            payload = json.loads(machine.getvalue())
            self.assertIs(payload['passed'], False)
            self.assertEqual(payload['failed_steps'], ['manifest'])
            self.assertIs(payload['manifest']['agree'], False)

    def test_report_runs_consumer_steps_and_surfaces_split_disagreement(self):
        row = {
            'canonical_id': 'code-repair:test',
            'split': 'train',
            'text': 'prompt' + probe.SEPARATOR + 'def corrected():\n    return 1\n',
            'completion_start_char': len('prompt' + probe.SEPARATOR),
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            records = root / 'records.jsonl'
            records.write_text(json.dumps(row) + '\n', encoding='utf-8')
            manifest = root / 'MANIFEST.json'
            manifest.write_text(json.dumps({
                'files': {
                    'agoge/code_repair_v1.jsonl': hashlib.sha256(records.read_bytes()).hexdigest(),
                },
                'tables': {'dispositions': {'exported': 1}},
                'run': {'split_policy': {'seed': 1, 'salt': 'x', 'weights': {'train': 100}}},
            }), encoding='utf-8')
            args = SimpleNamespace(
                agoge_jsonl=records, manifest=manifest, source_path='source.jsonl',
                source_revision=None, dataset_version=None, freeze_into=None,
                config=Path('config.yaml'), tokenizer_revision=None,
            )
            loaded = {'normalized_rows': 1, 'frozen_split_records': 1, 'records': [object()]}
            labels = {'tokenizer': 'local/model', 'rows': [], 'config': {'revision': 'a' * 40}}
            with (
                mock.patch.object(probe, '_load_proof', return_value=loaded),
                mock.patch.object(probe, '_spec', return_value=object()),
                mock.patch.object(
                    probe, '_split_agreement',
                    return_value={'agree': False, 'disagree': ['code-repair:test']},
                ),
                mock.patch.object(probe, '_labels', return_value=labels),
            ):
                report = probe._report(args)

        self.assertIs(report['passed'], False)
        self.assertEqual(report['failed_steps'], ['split_agreement'])
        self.assertEqual(report['load'], {
            'normalized_rows': 1, 'frozen_split_records': 1,
        })
        self.assertNotIn('policy', report)
        self.assertEqual(report['split_agreement']['disagree'], ['code-repair:test'])
        self.assertEqual(report['config'], {'revision': 'a' * 40})
        self.assertNotIn('config', report['labels'])


if __name__ == "__main__":
    unittest.main()
