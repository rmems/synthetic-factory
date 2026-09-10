"""Trusted export boundaries reject internally consistent metadata forgeries."""
import copy
import importlib
from types import SimpleNamespace
import unittest
import tempfile
import json
import hashlib
import contextlib
import io
import shutil
from dataclasses import replace
from pathlib import Path
from unittest import mock

from tests.code_repair_test_support import fixture, smoke_run, envelope, oc, views
from scripts import agoge_consumer_probe as probe
from tests.test_code_repair_export import run_copy, request, restamp
from tests.code_repair_test_support import FIXTURE_CATALOG
from tests.code_repair_test_support import cli
from code_repair import (
    catalog, export, generate, replay, run_validation, trusted_replay, vocabulary as cv,
)


class _ExplodingDict(dict):
    def __init__(self, *args, explode_on_get=None, explode_on_iter=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.explode_on_get = explode_on_get
        self.explode_on_iter = explode_on_iter

    def __getitem__(self, key):
        if key == self.explode_on_get:
            raise AssertionError(f"read past first mismatch: {key}")
        return super().__getitem__(key)

    def __iter__(self):
        if self.explode_on_iter:
            raise AssertionError("iterated past first mismatch")
        return super().__iter__()


class SharedValidation(unittest.TestCase):
    def test_validation_helpers_stop_at_the_first_mismatch(self):
        header = _ExplodingDict({'format': 'wrong'}, explode_on_get='family')
        with self.subTest(helper='run header'):
            self.assertFalse(run_validation._run_header_matches(header))

        execution = SimpleNamespace(
            run=_ExplodingDict({'produced_at': 'wrong'}, explode_on_get='per_program_cap'),
            candidates_sha256='unused',
        )
        with self.subTest(helper='run execution'):
            self.assertFalse(run_validation._run_execution_matches(execution))

        skips = _ExplodingDict({'invalid': True}, explode_on_iter=True)
        with self.subTest(helper='skips'):
            self.assertFalse(run_validation._skips_match({'skips': skips}))

    def test_catalog_free_shape_allows_unavailable_environment_metadata(self):
        record = copy.deepcopy(smoke_run()[1][0])
        record['oracle']['fingerprint'].update(implementation=None, platform=None)
        record['provenance']['record_sha256'] = envelope.record_digest(record)
        self.assertEqual(self.validator('validate_record')(record), [])

    def test_catalog_free_validation_rejects_malformed_mandatory_fields(self):
        validate = self.validator('validate_record')
        changes = [('intervention', {}), ('intervention.operator', []),
                   ('intervention.draw_index', True), ('scenario.source.family', []),
                   ('oracle.configuration.timeout_s', 'invalid')]
        for original in smoke_run()[1]:
            self.assertEqual(validate(original), [])
            for path, value in changes:
                record = copy.deepcopy(original)
                parent = record
                keys = path.split('.')
                for key in keys[:-1]:
                    parent = parent[key]
                parent[keys[-1]] = value
                record['provenance']['record_sha256'] = envelope.record_digest(record)
                with self.subTest(record=record['id'], field=path):
                    self.assertTrue(validate(record))

    def validator(self, name):
        try:
            module = importlib.import_module('code_repair.validation')
        except ModuleNotFoundError:
            module = None
        self.assertTrue(callable(getattr(module, name, None)), 'shared pure validator is missing')
        return getattr(module, name)

    def test_every_natural_outcome_is_valid_without_executing(self):
        validate = self.validator('validate_record')
        for record in smoke_run()[1]:
            with self.subTest(record=record['id']):
                self.assertEqual(validate(record, catalog=fixture()), [])

    def test_nonpositive_inner_evidence_digest_cannot_be_restamped(self):
        validate = self.validator('validate_record')
        record = copy.deepcopy(next(r for r in smoke_run()[1] if not views.is_positive(r)))
        record['result']['evidence_sha256'] = '0' * 64
        record['provenance']['record_sha256'] = envelope.record_digest(record)
        self.assertTrue(validate(record, catalog=fixture()))

    def test_nonpositive_public_evidence_is_bound_to_observed_rows(self):
        validate = self.validator('validate_record')
        record = copy.deepcopy(next(r for r in smoke_run()[1] if not views.is_positive(r)))
        record['result']['public_failure_omitted'] += 1
        record['provenance']['record_sha256'] = envelope.record_digest(record)
        self.assertTrue(validate(record, catalog=fixture()))

    def test_catalog_binds_public_tests_and_intervention_for_nonpositive_rows(self):
        validate = self.validator('validate_record')
        base = next(r for r in smoke_run()[1] if not views.is_positive(r))
        for section, field, value in [('intervention', 'variant', 999),
                                       ('scenario', 'public_tests', {'kind': 'doctest', 'examples': []})]:
            record = copy.deepcopy(base)
            record[section][field] = value
            record['provenance']['record_sha256'] = envelope.record_digest(record)
            self.assertTrue(validate(record, catalog=fixture()))

    def test_run_validates_complete_metadata_and_exact_captured_digest(self):
        validate = self.validator('validate_run')
        run, records, _ = smoke_run()
        digest = run['candidates_sha256']
        self.assertEqual(validate(run, records, catalog=fixture(), candidates_sha256=digest), [])
        edits = {'count': run['count'] + 1, 'generator': {'name': 'forged', 'version': '2.0.0'},
                 'timeout_s': 999, 'seed': run['seed'] + 1, 'produced_at': 'forged',
                 'harness_sha256': '0' * 64, 'programs': {}, 'reasons': {}, 'records': True}
        for key, value in edits.items():
            with self.subTest(field=key):
                changed = copy.deepcopy(run)
                changed[key] = value
                self.assertTrue(validate(changed, records, catalog=fixture(), candidates_sha256=digest))
        self.assertTrue(validate(run, records, catalog=fixture(), candidates_sha256='0' * 64))

    def test_malformed_records_and_runs_return_findings(self):
        record_validator = self.validator('validate_record')
        run_validator = self.validator('validate_run')
        for value in (None, [], {}, {'format': 'code-repair-run/2'}):
            self.assertTrue(record_validator(value, catalog=fixture()))
            self.assertTrue(run_validator(value, [], catalog=fixture(), candidates_sha256='0' * 64))

    def test_empty_run_still_enforces_seed_count_stamp_and_numeric_domains(self):
        validate = self.validator('validate_run')
        run, records, _ = smoke_run()
        for key, value in [('seed', -1), ('seed', 2**64), ('count', 0),
                           ('count', cv.MAX_COUNT + 1), ('produced_at', 'no timestamp'),
                           ('timeout_s', 10**400)]:
            with self.subTest(key=key, value=str(value)[:30]):
                self.assertTrue(validate({**run, key: value}, [], catalog=fixture(),
                                         candidates_sha256=run['candidates_sha256']))
        corrupted = copy.deepcopy(run)
        program_id = next(k for k, v in corrupted['programs'].items() if v['records'] == 1)
        corrupted['programs'][program_id]['records'] = True
        self.assertTrue(validate(corrupted, records, catalog=fixture(),
                                 candidates_sha256=run['candidates_sha256']))


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
        with mock.patch.object(probe, '_make_spec', side_effect=ValueError('bad policy')):
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
            self.assertEqual(payload['manifest']['agree'], False)

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


class FreshReplay(unittest.TestCase):
    def test_public_replay_mapping_retains_protocol_key_order(self):
        run, records, _run_dir = smoke_run()
        report = trusted_replay.replay_records(
            run, records, catalog=fixture(), candidates_sha256=run['candidates_sha256'],
        )
        self.assertEqual(
            list(report),
            ['run_identity', 'catalog', 'harness_sha256', 'interpreter',
             'status', 'records', 'counts'],
        )

    def test_malformed_run_catalog_refuses_api_and_cli_without_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir, _ = run_copy(root)
            path = run_dir / generate.RUN_FILENAME
            run = json.loads(path.read_text())
            bad = [None, [], {}, {'catalog_id': [], 'programs_sha256': 123}]
            for index, value in enumerate(['missing'] + bad):
                changed = {**run, 'catalog': value}
                if value == 'missing':
                    changed.pop('catalog')
                path.write_text(json.dumps(changed))
                out = root / f'replay-{index}'
                with self.subTest(catalog=value):
                    try:
                        replay.run(replay.ReplayRequest(run_dir, FIXTURE_CATALOG, out))
                    except Exception as exc:
                        self.assertIsInstance(exc, cv.RepairRefusal)
                    else:
                        self.fail('malformed catalog was accepted')
                    self.assertFalse(out.exists())
                    captured = io.StringIO()
                    try:
                        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
                            code = cli.run(['replay', '--run', str(run_dir), '--catalog',
                                            str(FIXTURE_CATALOG), '--out', str(out), '--json'])
                    except Exception as exc:
                        self.fail(f'CLI leaked {type(exc).__name__}')
                    self.assertNotEqual(code, 0)
                    self.assertIn('RECORD_MALFORMED', captured.getvalue())
                    self.assertFalse(out.exists())

    def test_report_environment_metadata_cannot_be_changed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = smoke_run()[2]
            report_dir = root / 'replay'
            report = replay.run(replay.ReplayRequest(run_dir, FIXTURE_CATALOG, report_dir))
            report['harness_sha256'] = '0' * 64
            (report_dir / replay.REPLAY_FILENAME).write_text(json.dumps(report))
            with self.assertRaises(cv.RepairRefusal):
                export.run(request(run_dir, root / 'export', report_dir))
            self.assertFalse((root / 'export').exists())

    def test_export_propagates_non_mit_catalog_license(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pinned = root / 'catalog'
            shutil.copytree(FIXTURE_CATALOG, pinned)
            rows = [r for _, r in oc.read_jsonl(pinned / catalog.PROGRAMS_FILENAME)]
            for row in rows:
                row['upstream']['license'] = 'Apache-2.0'
            (pinned / catalog.PROGRAMS_FILENAME).unlink()
            oc.write_jsonl(pinned / catalog.PROGRAMS_FILENAME, rows)
            metadata_path = pinned / catalog.CATALOG_FILENAME
            meta = json.loads(metadata_path.read_text())
            meta['upstream']['license'] = 'Apache-2.0'
            meta['programs_sha256'] = hashlib.sha256((pinned / catalog.PROGRAMS_FILENAME).read_bytes()).hexdigest()
            metadata_path.write_text(json.dumps(meta))
            generate.run(generate.RunRequest(pinned, root / 'run', 20260908, 12,
                                              '2026-09-08T00:00:00.000Z'))
            manifest = export.run(export.ExportRequest(root / 'run', root / 'export', catalog_dir=pinned))
            self.assertEqual(manifest['rights']['upstream_license'], 'Apache-2.0')

    def test_coordinated_false_groups_are_recomputed(self):
        from code_repair.validation import validate_run
        run, records, _ = smoke_run()
        records = copy.deepcopy(records)
        pinned = fixture()
        programs = tuple(replace(p, group_id='forged') for p in pinned.programs)
        forged = replace(pinned, programs=programs)
        for record in records:
            record['provenance']['split_lineage']['group_id'] = 'forged'
            restamp(record)
        data = ''.join(oc.canonical_json(r) + '\n' for r in records).encode()
        digest = hashlib.sha256(data).hexdigest()
        run = {**run, 'candidates_sha256': digest}
        self.assertIn(cv.EXPORT_CATALOG_MISMATCH,
                      validate_run(run, records, catalog=forged, candidates_sha256=digest))

    def test_consistently_edited_failure_report_cannot_grant_replay_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir, records = run_copy(root)
            positive = next(r for r in records if views.is_positive(r))
            positive['oracle']['fingerprint']['python'] = '0.0'
            restamp(positive)
            candidates = run_dir / generate.CANDIDATES_FILENAME
            candidates.unlink()
            oc.write_jsonl(candidates, records)
            meta_file = run_dir / generate.RUN_FILENAME
            run = json.loads(meta_file.read_text())
            run['candidates_sha256'] = hashlib.sha256(candidates.read_bytes()).hexdigest()
            meta_file.write_text(json.dumps(run))
            report_dir = root / 'replay'
            report = replay.run(replay.ReplayRequest(run_dir, FIXTURE_CATALOG, report_dir))
            self.assertEqual(report['status'], 'failed')
            report['status'] = 'passed'
            for entry in report['records']:
                if entry['status'] == 'replayed':
                    entry['code'] = cv.REPLAY_PASSED
            report['counts'].update(passed=report['counts']['positives'], failed=0, failed_by_code={})
            (report_dir / replay.REPLAY_FILENAME).write_text(json.dumps(report))
            with self.assertRaises(cv.RepairRefusal):
                export.run(request(run_dir, root / 'export', report_dir))
            self.assertFalse((root / 'export').exists())
