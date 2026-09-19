"""Native backend selection cannot silently execute reference physics."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

import oracle_generate
from oracle_grounded import families, oracles, record, rng


class RustBackendSelectionTests(unittest.TestCase):
    def test_cli_accepts_explicit_rust_backend(self):
        args = oracle_generate.parse_args(['--backend', 'rust', 'unused'])
        self.assertEqual(args.backend, 'rust')

    def test_reference_cli_ignores_ambient_runtime_commands(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'run'
            env = {'SF_ORACLE_AXON_ENCODER_CMD': '/definitely-not-a-runtime'}
            with patch.dict(os.environ, env):
                status = oracle_generate.main(['--backend', 'reference', '--count', '1',
                                               '--family', families.ENCODER_FAMILY, str(out)])
            self.assertEqual(status, 0)
            import json
            item = json.loads(next(out.rglob('accepted-*.jsonl')).read_text())
            self.assertEqual(item['oracle']['implementation'], 'reference')

    def test_native_profile_uses_distinct_scenario_model(self):
        selector = getattr(families, 'spec_for_profile', None)
        self.assertIsNotNone(selector, 'Native profiles need an explicit spec selector')
        spec = selector(families.NEURON_FAMILY, 'neuromod-lif-v1')
        scenario, intervention, candidate = spec.propose(rng.Rng(9))
        self.assertEqual(scenario['profile'], 'neuromod-lif-v1')
        self.assertNotIn('adaptation_b', scenario['parameters'])
        self.assertIsNone(candidate)
        self.assertIn(intervention['parameter'], ('threshold', 'decay', 'input_scale'))

    def test_rust_unsupported_family_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'run'
            status = oracle_generate.main(['--backend', 'rust', '--family', families.MEMORY_FAMILY, str(out)])
            self.assertNotEqual(status, 0)
            self.assertFalse(out.exists())

    def test_rust_without_executable_never_falls_back(self):
        run = record.RecordRunContext(backend='rust')
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(oracles.OracleError, 'executable|SF_ORACLE_RUST_BIN'):
                record.build_record(
                    families.ENCODER_FAMILY,
                    0,
                    seed=1,
                    run=run,
                )


if __name__ == '__main__':
    unittest.main()
