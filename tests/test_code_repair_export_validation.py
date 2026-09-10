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
from fractions import Fraction
from pathlib import Path

from tests.code_repair_test_support import fixture, smoke_run, envelope, oc, views
from scripts import agoge_consumer_probe as probe
from tests.test_code_repair_export import run_copy, request, restamp
from tests.code_repair_test_support import FIXTURE_CATALOG
from tests.code_repair_test_support import cli
from code_repair import (
    catalog, export, generate, publication, replay, run_validation, trusted_replay,
    validation, vocabulary as cv,
)
from code_repair._contract import ExactJSONFloat, exact_fraction


class ExactDecoding(unittest.TestCase):
    def test_candidate_decoders_refuse_an_out_of_range_token_stamped_as_rounded(self):
        record = copy.deepcopy(smoke_run()[1][0])
        record['oracle']['configuration']['timeout_s'] = 60.0
        record['oracle']['configuration']['limits']['cpu_s'] = 62
        restamp(record)
        self.assertEqual(validation.validate_record(record), [])
        payload = (oc.canonical_json(record) + '\n').encode().replace(
            b'"timeout_s":60.0', b'"timeout_s":60.0000000000000000000001')
        for loader in (export._load_records, lambda raw: publication._records(raw)[0]):
            with self.subTest(loader=loader):
                self.assertTrue(validation.validate_record(loader(payload)[0]))

    def test_run_and_candidate_decoders_preserve_supported_decimal_tokens(self):
        run, originals, _ = smoke_run()
        for token in ('2.0', '2e0', '2.0000000000000000000001'):
            with self.subTest(token=token):
                record = copy.deepcopy(originals[0])
                record['oracle']['configuration']['timeout_s'] = ExactJSONFloat(token)
                restamp(record)
                payload = (oc.canonical_json(record) + '\n').encode().replace(
                    b'"timeout_s":2.0', f'"timeout_s":{token}'.encode())
                candidates = (export._load_records(payload.replace(b'\n', b'\r\n'))[0],
                              publication._records(payload)[0][0])
                for decoded in candidates:
                    self.assertEqual(exact_fraction(decoded['oracle']['configuration']['timeout_s']),
                                     Fraction(token))
                    self.assertEqual(validation.validate_record(decoded), [])
                run_bytes = oc.canonical_json(run).encode().replace(
                    b'"timeout_s":2.0', f'"timeout_s":{token}'.encode())
                self.assertEqual(exact_fraction(export._load_run(run_bytes)['timeout_s']),
                                 Fraction(token))
                self.assertTrue(run_validation._valid_timeout(export._load_run(run_bytes)['timeout_s']))

    def test_run_parser_does_not_round_an_out_of_range_timeout(self):
        run = {**smoke_run()[0], 'timeout_s': 60.0}
        raw = oc.canonical_json(run).encode().replace(
            b'"timeout_s":60.0', b'"timeout_s":60.0000000000000000000001')
        self.assertGreater(exact_fraction(export._load_run(raw)['timeout_s']), Fraction(60))
        self.assertFalse(run_validation._valid_timeout(export._load_run(raw)['timeout_s']))

    def test_run_identity_does_not_equate_distinct_exact_timeouts(self):
        run, records, _ = smoke_run()
        changed = {**run, 'timeout_s': ExactJSONFloat('2.0000000000000000000001')}
        self.assertFalse(run_validation._oracle_identity_matches(records[0], changed))

    def test_export_refuses_rounded_timeout_forgery_without_output(self):
        with tempfile.TemporaryDirectory() as directory:
            run_dir, records = run_copy(directory)
            for record in records:
                record['oracle']['configuration'].update(timeout_s=60.0)
                record['oracle']['configuration']['limits']['cpu_s'] = 62
                restamp(record)
            data = ('\n'.join(oc.canonical_json(r) for r in records) + '\n').encode().replace(
                b'"timeout_s":60.0', b'"timeout_s":60.0000000000000000000001')
            (run_dir / generate.CANDIDATES_FILENAME).write_bytes(data)
            run = {**smoke_run()[0], 'timeout_s': 60.0,
                   'candidates_sha256': hashlib.sha256(data).hexdigest()}
            (run_dir / generate.RUN_FILENAME).write_text(oc.canonical_json(run))
            output = Path(directory) / 'must-refuse'
            with self.assertRaises(cv.RepairRefusal):
                export.run(request(run_dir, output))
            self.assertFalse(output.exists())

    def test_export_accepts_supported_timeout_spellings_and_crlf(self):
        for token in (b'2.0', b'2e0', b'2.0000000000000000000001'):
            with self.subTest(token=token), tempfile.TemporaryDirectory() as directory:
                run_dir, records = run_copy(directory)
                candidates = run_dir / generate.CANDIDATES_FILENAME
                data = candidates.read_bytes().replace(b'"timeout_s":2.0', b'"timeout_s":' + token)
                data = data.replace(b'\n', b'\r\n')
                candidates.write_bytes(data)
                run = {**smoke_run()[0], 'candidates_sha256': hashlib.sha256(data).hexdigest()}
                run_bytes = oc.canonical_json(run).encode().replace(
                    b'"timeout_s":2.0', b'"timeout_s":' + token)
                (run_dir / generate.RUN_FILENAME).write_bytes(run_bytes)
                manifest = export.run(request(run_dir, Path(directory) / 'valid-export'))
                self.assertEqual(manifest['tables']['records'], len(records))


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
