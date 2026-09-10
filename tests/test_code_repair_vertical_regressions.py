"""Regression evidence for PR197 generation and rendering trust boundaries."""
import copy
import dataclasses
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tests.code_repair_test_support import (
    FIXTURE_CATALOG, PINNED_AT, SEED, FakeExecutor, catalog, generate, mutate, oc,
    report, rows, smoke_run, verify, views, envelope, vocabulary as cv,
)
from tests.test_code_repair_catalog import copied_fixture, rewrite_programs
from tests.test_code_repair_cli import invoke
from tests.test_code_repair_verify import phases, CERTIFIED
from code_repair import record_validation


class VerticalRegressions(unittest.TestCase):
    def positive(self):
        return copy.deepcopy(next(r for r in smoke_run()[1] if r['result']['outcome'] == 'accepted'))

    def test_run_summary_pins_exact_candidate_bytes(self):
        summary, _, directory = smoke_run()
        self.assertEqual(summary.get('candidates_sha256'), hashlib.sha256(
            (directory / 'candidates.jsonl').read_bytes()).hexdigest())
        self.assertEqual(summary, json.loads((directory / 'RUN.json').read_text()))

    def test_nested_definitions_do_not_offer_metadata_sites(self):
        text = ('def f():\n    @deco(1 < 2)\n    def g(x=(2 < 3)) -> (3 < 4):\n'
                '        return x < 5\n    class C(Base(4 < 5)):\n'
                '        def m(self, x=(5 < 6)):\n            return x < 7\n'
                '    return 6 < 7\n')
        self.assertEqual([s.lineno for s in mutate.sites(text, 'f')], [4, 7, 8])

    def test_truncated_fabricated_output_is_rejected(self):
        record = self.positive()
        entry = record['result']['public_failure_evidence'][0]
        entry.update(got='fabricated', truncated=True)
        row = {'prompt': views.render_prompt(views.public_view(record)),
               'completion': views.completion_of(record)}
        self.assertIn(cv.LEAK_PUBLIC_EVIDENCE_NOT_FROM_ROWS, views.view_findings(record, row))

    def test_coherent_test_metadata_forgery_is_rejected(self):
        record = self.positive()
        entry = record['result']['public_failure_evidence'][0]
        example = next(e for e in record['scenario']['public_tests']['examples']
                       if e['example_id'] == entry['example_id'])
        entry['source'] = example['source'] = 'fabricated()\n'
        row = {'prompt': views.render_prompt(views.public_view(record)),
               'completion': views.completion_of(record)}
        self.assertIn(cv.LEAK_PUBLIC_EVIDENCE_NOT_FROM_ROWS, views.view_findings(record, row))

    def test_relabelled_rejection_is_not_positive(self):
        record = copy.deepcopy(next(r for r in smoke_run()[1]
                                   if 'MUTANT_NO_PUBLIC_FAILURE' in r['result']['reason_codes']))
        record['result'].update(outcome='accepted', oracle_status='validated')
        record['provenance']['record_sha256'] = envelope.record_digest(record)
        self.assertFalse(views.is_positive(record))

    def test_replaced_completion_cannot_reuse_old_execution(self):
        record = self.positive()
        repair = record['candidate_prediction']['predicted_repair']
        repair['files']['program.py'] = 'arbitrary replacement\n'
        repair['sha256'] = record['result']['repaired_sha256'] = catalog.sha256_text('arbitrary replacement\n')
        record['provenance']['record_sha256'] = envelope.record_digest(record)
        row = {'prompt': views.render_prompt(views.public_view(record)),
               'completion': views.completion_of(record)}
        self.assertIn(cv.LEAK_COMPLETION_NOT_VERIFIED, views.view_findings(record, row))

    def test_oversized_example_evidence_is_omitted_within_budget(self):
        example = catalog.Example('f:0', 'x' * 5000, '1\n', None)
        entries, omitted = verify.public_evidence(report(rows('public', 1, (0,))), (example,))
        self.assertLessEqual(len(verify.render_evidence(entries, omitted)), cv.MAX_EVIDENCE_CHARS)
        self.assertEqual(omitted, 1)

    def test_agoge_boundary_is_constructed_unicode_offset(self):
        record = self.positive()
        record['scenario']['task_specification'] += '\n雪🙂' + cv.AGOGE_SEPARATOR
        record['provenance']['record_sha256'] = envelope.record_digest(record)
        row = views.agoge_row(record)
        offset = row.get('completion_start_char')
        self.assertIs(type(offset), int)
        self.assertEqual(row['text'][offset:], views.completion_of(record))
        self.assertEqual(row['text'][:offset], views.sft_row(record)['prompt'] + cv.AGOGE_SEPARATOR)

    def test_oracle_labels_in_source_metadata_are_refused(self):
        for key in ('reference', 'public_failure_omitted'):
            record = self.positive()
            record['scenario']['source']['upstream'][key] = 'forged'
            self.assertTrue(oc.check_oracle_label_leak(record, record['id']), key)

    def test_nondeterministic_original_stops_before_mutation(self):
        calls = {}
        def original(job):
            calls[job.module_text] = calls.get(job.module_text, 0) + 1
            return report(({'id': 'public:0', 'status': 'pass',
                            'got': str(calls[job.module_text])},), rows('hidden', len(job.cases)))
        fake = FakeExecutor({'original': original, 'original_repeat': original,
                             'mutant': lambda job: report(rows('public', 1, (0,)),
                                                          rows('hidden', len(job.cases), (0,))),
                             'repaired': original})
        with tempfile.TemporaryDirectory() as root:
            summary = generate.run(generate.RunRequest(FIXTURE_CATALOG, Path(root)/'run',
                                                        SEED, 1, PINNED_AT), fake)
        self.assertEqual(summary['reasons'], {'SOURCE_NONDETERMINISTIC': 1})
        self.assertFalse(any(j.label.startswith('mutant:') for j in fake.jobs))

    def test_direct_sft_projection_refuses_fabricated_evidence(self):
        record = self.positive()
        record['result']['public_failure_evidence'][0]['got'] = 'fabricated'
        record['provenance']['record_sha256'] = envelope.record_digest(record)
        with self.assertRaises(cv.RepairRefusal):
            views.sft_row(record)

    def test_cli_malformed_family_fields_are_coded_refusals(self):
        for field, value in (('example_id', 'bad'), ('example_id', 'f:-1'),
                             ('example_id', 'f:01'), ('got', {}), ('truncated', 1)):
            record = self.positive()
            record['result']['public_failure_evidence'][0][field] = value
            record['provenance']['record_sha256'] = envelope.record_digest(record)
            with tempfile.TemporaryDirectory() as root:
                oc.write_jsonl(Path(root)/'candidates.jsonl', [record])
                code, output, _ = invoke(['render', root, record['id'], '--json'])
            self.assertEqual(code, 2, (field, value, output))
            self.assertEqual(json.loads(output)['code'], 'RECORD_MALFORMED')
            self.assertNotIn('sft', json.loads(output))

    def test_shape_validation_guards_every_later_source_binding_read(self):
        paths = (('scenario', 'source', 'module_sha256'),
                 ('scenario', 'broken_program', 'sha256'),
                 ('candidate_prediction', 'predicted_repair', 'sha256'),
                 ('oracle', 'configuration', 'hidden_check', 'kind'),
                 ('oracle', 'configuration', 'hidden_check', 'reference_sha256'),
                 ('provenance', 'split_lineage', 'lineage_id'))
        for path in paths:
            record = self.positive()
            node = record
            for key in path[:-1]:
                node = node[key]
            del node[path[-1]]
            record['provenance']['record_sha256'] = envelope.record_digest(record)
            with self.subTest(path=path), self.assertRaises(cv.RepairRefusal):
                record_validation.validate_shape(record)

    def test_cli_invalid_broken_source_is_a_coded_refusal(self):
        record = self.positive()
        broken = record['scenario']['broken_program']
        broken['files']['program.py'] = 'def broken(:\n'
        broken['sha256'] = record['result']['broken_sha256'] = catalog.sha256_text(
            broken['files']['program.py'])
        record['result']['phases']['mutant']['module_sha256'] = broken['sha256']
        record['result']['evidence_sha256'] = verify.result_hash(record['result']['phases'])
        record['provenance']['record_sha256'] = envelope.record_digest(record)
        with tempfile.TemporaryDirectory() as root:
            oc.write_jsonl(Path(root)/'candidates.jsonl', [record])
            code, output, _ = invoke(['render', root, record['id'], '--json'])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(output)['code'], 'RECORD_MALFORMED')
        self.assertNotIn('sft', json.loads(output))

    def failed_phase_record(self, status, flag):
        record = copy.deepcopy(next(r for r in smoke_run()[1]
                                    if r['result']['reason_codes'] == ['MUTANT_TIMEOUT']))
        block = record['result']['phases']['mutant']
        block.update(status=status, load_ok=False)
        if flag == 'missing':
            del block['limits_applied']
        else:
            block['limits_applied'] = flag
        block['sha256'] = catalog.sha256_text(oc.canonical_json([block['public'], block['hidden']]))
        record['result']['evidence_sha256'] = verify.result_hash(record['result']['phases'])
        record['provenance']['record_sha256'] = envelope.record_digest(record)
        return record

    def test_failed_phases_require_a_valid_limits_field_before_reconstruction(self):
        for status in ('timeout', 'harness_error', 'ok'):
            for flag in ('missing', 0, 1, 'false', {}):
                record = self.failed_phase_record(status, flag)
                with self.subTest(status=status, flag=flag):
                    with self.assertRaises(cv.RepairRefusal):
                        record_validation.validate_shape(record)
                    with tempfile.TemporaryDirectory() as root:
                        oc.write_jsonl(Path(root)/'candidates.jsonl', [record])
                        code, output, _ = invoke(['render', root, record['id'], '--json'])
                    self.assertEqual(code, 2)
                    self.assertEqual(json.loads(output)['code'], 'RECORD_MALFORMED')

    def test_failed_phase_limits_flags_survive_validated_reconstruction(self):
        for status in ('timeout', 'harness_error', 'ok'):
            for flag in (False, None, True):
                record = self.failed_phase_record(status, flag)
                with self.subTest(status=status, flag=flag):
                    record_validation.validate_shape(record)
                    phase = verify.phases_from_blocks(record['result']['phases']).mutant
                    self.assertIs(phase.environment['limits_applied'], flag)
                    self.assertEqual(verify.phase_block(phase), record['result']['phases']['mutant'])

    def test_evidence_reordering_and_shortening_is_detected(self):
        record = copy.deepcopy(next(r for r in smoke_run()[1]
                                    if len(r['result']['public_failure_evidence']) >= 2))
        self.assertGreaterEqual(len(record['result']['public_failure_evidence']), 2)
        for entries in (list(reversed(record['result']['public_failure_evidence'])), []):
            edited = copy.deepcopy(record)
            edited['result']['public_failure_evidence'] = entries
            row = {'prompt': views.render_prompt(views.public_view(edited)),
                   'completion': views.completion_of(edited)}
            self.assertIn(cv.LEAK_PUBLIC_EVIDENCE_NOT_FROM_ROWS, views.view_findings(edited, row))

    def test_missing_limits_are_refused_before_more_execution(self):
        fake = FakeExecutor({'original': lambda job: dataclasses.replace(
            report(rows('public', 1)), environment={'limits_applied': False})})
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(cv.RepairRefusal) as raised:
                generate.run(generate.RunRequest(FIXTURE_CATALOG, Path(root)/'run', SEED, 1, PINNED_AT), fake)
            self.assertEqual(raised.exception.code, 'SANDBOX_UNAVAILABLE')
            self.assertFalse((Path(root)/'run').exists())
        self.assertEqual(len(fake.jobs), 1)

    def test_decision_table_never_certifies_unlimited_execution(self):
        reports = phases()
        unlimited = dataclasses.replace(reports.original, environment={'limits_applied': False})
        verdict = verify.decide(dataclasses.replace(reports, original=unlimited,
                                                   original_repeat=unlimited, repaired=unlimited), CERTIFIED)
        self.assertFalse(verdict.accepted)
        self.assertEqual(verdict.oracle_status, 'invalid')

    def test_agoge_embedded_program_separator_does_not_change_boundary(self):
        with tempfile.TemporaryDirectory() as root:
            directory = copied_fixture(root)
            def edit(row):
                text = '"""雪🙂' + cv.AGOGE_SEPARATOR + '"""\n' + row['module']['text']
                row['module'] = {'text': text, 'sha256': catalog.sha256_text(text)}
            rewrite_programs(directory, edit)
            out = Path(root)/'run'
            generate.run(generate.RunRequest(directory, out, SEED, 1, PINNED_AT))
            record = next(oc.iter_jsonl(out/'candidates.jsonl'))[1]
            row = views.agoge_row(record)
        offset = row['completion_start_char']
        self.assertEqual(row['text'][offset:], views.completion_of(record))
        self.assertIn('雪🙂', row['text'][:offset])
        self.assertGreaterEqual(row['text'][:offset].count(cv.AGOGE_SEPARATOR), 2)
        self.assertGreater(len(row['text'][:offset].encode('utf-8')), offset)

    def test_catalog_revisions_have_distinct_canonical_ids(self):
        with tempfile.TemporaryDirectory() as root:
            directory = copied_fixture(root)
            rewrite_programs(directory, lambda row: row['upstream'].update(review_revision='new'))
            out = Path(root)/'run'
            generate.run(generate.RunRequest(directory, out, SEED, 1, PINNED_AT))
            record = next(oc.iter_jsonl(out/'candidates.jsonl'))[1]
        self.assertNotEqual(record['id'], smoke_run()[1][0]['id'])

    def test_real_ellipsis_output_is_checked_for_full_observation_determinism(self):
        with tempfile.TemporaryDirectory() as root:
            directory = copied_fixture(root)
            def edit(row):
                function = row['upstream']['function']
                text = (f"def {function}(x=0):\n    '''\n"
                        "    >>> import uuid; print('x' * 2100 + str(uuid.uuid4()))  # doctest: +ELLIPSIS\n"
                        "    xxx...\n    '''\n    return x < 0\n")
                row['module'] = {'text': text, 'sha256': catalog.sha256_text(text)}
                examples = catalog.examples_of(text, function)
                row['public'] = {'example_count': 1, 'examples_sha256': catalog.examples_sha256(examples)}
                row['hidden']['cases'] = [{'args': '(0,)', 'want': 'False'}]
            rewrite_programs(directory, edit)
            out = Path(root)/'run'
            summary = generate.run(generate.RunRequest(directory, out, SEED, 1, PINNED_AT))
            record = next(oc.iter_jsonl(out/'candidates.jsonl'))[1]
        self.assertEqual(summary['reasons'], {'SOURCE_NONDETERMINISTIC': 1})
        phases = record['result']['phases']
        left, right = phases['original']['public'][0], phases['original_repeat']['public'][0]
        self.assertEqual(left['got'], right['got'])
        self.assertNotEqual(left['got_sha256'], right['got_sha256'])
        self.assertIsNone(phases['mutant'])


if __name__ == '__main__':
    unittest.main()
