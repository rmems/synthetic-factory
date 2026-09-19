"""Git checkout conversion cannot alter independently sealed runtime inputs."""
import subprocess  # nosec B404 -- fixed git argv reads committed blobs only
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class OracleCheckoutBytes(unittest.TestCase):
    def test_crlf_checkout_preserves_license_and_native_source_bytes(self):
        # Use one committed LF blob under each actual target path's attributes.
        original = subprocess.check_output(  # nosec B603 -- fixed git argv, no shell
            ['/usr/bin/git', 'show', 'HEAD:LICENSE'], cwd=ROOT)
        for path in ('LICENSE', 'Cargo.toml', 'Cargo.lock', 'rust/sf-oracle/Cargo.toml',
                     'rust/sf-oracle/build.rs', 'rust/sf-oracle/src/encoder.rs'):
            with self.subTest(path=path):
                actual = subprocess.check_output([  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit  # nosec B603 -- fixed git argv, no shell
                    '/usr/bin/git', '-c', 'core.autocrlf=true', 'cat-file', '--filters',
                    f'--path={path}', 'HEAD:LICENSE'], cwd=ROOT)
                self.assertEqual(actual, original)
