"""Real crate execution survives authenticated assembly and local export."""

import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

import compose_curated
import export_hf
import oracle_generate
import oracle_validate
from oracle_grounded import canon, families, native_runtime, record

ROOT = Path(__file__).resolve().parents[1]
BINARY = ROOT / 'target/debug/sf-oracle'


@unittest.skipUnless(BINARY.is_file(), 'build the locked Rust oracle to run native integration')
class RustDatasetIntegration(unittest.TestCase):
    def test_both_families_replay_and_export_original_records(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, curated, exported = (root / name for name in ('source', 'curated', 'export'))
            with contextlib.redirect_stdout(io.StringIO()):
                status = oracle_generate.main(['--backend', 'rust', '--oracle-rust-bin', str(BINARY),
                                               '--count', '2', '--seed', '20260918', str(source)])
            self.assertEqual(status, 0)
            report, errors = oracle_validate.validate_run(
                oracle_validate.ValidationContext(source, oracle_rust_bin=str(BINARY))
            )
            self.assertEqual(errors, [])
            self.assertEqual(report['invalid'], 0, report)
            originals = [line for path in source.rglob('accepted-*.jsonl')
                         for line in path.read_bytes().splitlines()]
            self.assertEqual(len(originals), 4)
            summary = compose_curated.compose_run(
                compose_curated.ComposeRunContext(source, curated, oracle_rust_bin=str(BINARY))
            )
            self.assertEqual(summary['counts']['retained'], 4)
            self.assertTrue(summary['audit']['training_ready'], summary['audit'])
            entries = [json.loads(line) for line in (curated / 'manifest/compose-manifest.jsonl').read_text().splitlines()]
            retained = [(curated / entry['output_path']).read_bytes().splitlines()[entry['output_line'] - 1]
                        for entry in entries]
            self.assertCountEqual(retained, originals)
            result = export_hf.export_run(
                export_hf.ExportRequest(curated, exported, oracle_rust_bin=str(BINARY))
            )
            self.assertEqual(result['records'], 4)
            # Local export keeps the native payload files, beyond split indexing.
            for entry in entries:
                relative = entry['output_path']
                matches = list(exported.rglob(Path(relative).name))
                self.assertTrue(any(path.read_bytes() == (curated / relative).read_bytes()
                                    for path in matches), relative)

    def test_replay_detects_rehashed_measurement_and_identity_tampering(self):
        env = native_runtime.runtime_environ(BINARY, base={})
        for family in (families.ENCODER_FAMILY, families.NEURON_FAMILY):
            original = record.build_record(
                family, 0, seed=7, run=record.RecordRunContext(backend='rust', environ=env)
            )
            self.assertEqual(original['validation']['status'], 'accepted', original['validation'])
            for field in ('lock_sha256', 'adapter_source_sha256', 'executable_sha256'):
                item = copy.deepcopy(original)
                item['result']['measured']['identity'][field] = '0' * 64
                item['result_hash'] = canon.digest(item['result'])
                self.assertNotEqual(record.reproduce(item, environ=env)[0], 'reproduced')
            item = copy.deepcopy(original)
            measured = item['result']['measured']
            if family == families.ENCODER_FAMILY:
                measured['rate']['spikes'][0]['t_ms'] += 1
            else:
                measured['before']['v_trace'][0] += 0.1
            item['result_hash'] = canon.digest(item['result'])
            self.assertNotEqual(record.reproduce(item, environ=env)[0], 'reproduced')

    def test_missing_native_binary_cannot_replay_with_reference(self):
        env = native_runtime.runtime_environ(BINARY, base={})
        item = record.build_record(
            families.NEURON_FAMILY,
            0,
            seed=7,
            run=record.RecordRunContext(backend='rust', environ=env),
        )
        status, _ = record.reproduce(item, environ={})
        self.assertEqual(status, 'unavailable')


if __name__ == '__main__':
    unittest.main()
