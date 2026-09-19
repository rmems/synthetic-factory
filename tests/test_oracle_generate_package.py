"""Generation supports package entry points without pipelines on sys.path."""

import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class OracleGenerationPackageTests(unittest.TestCase):
    def run_isolated(self, source):
        environment = {key: value for key, value in os.environ.items()
                       if key != "PYTHONPATH" and not key.startswith("SF_ORACLE_")}
        return subprocess.run(
            [sys.executable, "-I", "-B", "-c", source, str(ROOT)],
            cwd=ROOT, env=environment, capture_output=True, text=True, timeout=30,
            check=False,
        )

    def test_package_imports_join_direct_names_without_path_injection(self):
        result = self.run_isolated("""
import sys
sys.path.insert(0, sys.argv[1])
import pipelines.oracle_generate as generate
import pipelines.oracle_generate_fs as filesystem
import pipelines.oracle_generate_records as records
import oracle_generate
import oracle_generate_fs
import oracle_generate_records
assert generate is oracle_generate
assert filesystem is oracle_generate_fs
assert records is oracle_generate_records
assert generate._GENERATION_FS.api is generate
assert generate._GENERATION_RECORDS.api is generate
assert sys.argv[1] + '/pipelines' not in sys.path
""")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_module_entrypoint_lists_families(self):
        result = self.run_isolated("""
import sys, runpy
sys.path.insert(0, sys.argv[1])
sys.argv = ['pipelines.oracle_generate', '--list-families']
runpy.run_module('pipelines.oracle_generate', run_name='__main__')
""")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('spike-encoder-equivalence-pairs', result.stdout)
        self.assertIn('neuron-dynamics-counterfactuals', result.stdout)

    def test_rust_preflight_reaches_missing_executable_refusal(self):
        result = self.run_isolated("""
import sys
sys.path.insert(0, sys.argv[1])
from pipelines import oracle_generate
status = oracle_generate.main(['--backend', 'rust', 'unused'])
assert status == 3, status
""")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('prebuilt executable', result.stderr)
