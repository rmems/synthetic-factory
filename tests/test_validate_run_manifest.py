"""Manifest replacement must never expose partially written validation output."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipelines import validate_run_cli


class ManifestPublicationTests(unittest.TestCase):
    def test_interrupted_write_preserves_previous_manifest(self):
        original_write = Path.write_text

        def interrupted_write(path, text, *args, **kwargs):
            original_write(path, text[:3], *args, **kwargs)
            raise OSError("injected write interruption")

        with tempfile.TemporaryDirectory() as raw:
            run_dir = Path(raw)
            manifest_path = run_dir / "manifest.json"
            previous = '{"previous": true}\n'
            manifest_path.write_text(previous)
            with mock.patch.object(Path, "write_text", interrupted_write):
                with self.assertRaisesRegex(OSError, "injected write interruption"):
                    validate_run_cli.main(
                        ["--write", raw], check_line=lambda obj, where: ([], "unknown")
                    )
            self.assertEqual(manifest_path.read_text(), previous)
            self.assertEqual(list(run_dir.iterdir()), [manifest_path])

    def test_reader_sees_previous_manifest_until_complete_replacement(self):
        original_replace = Path.replace
        with tempfile.TemporaryDirectory() as raw:
            run_dir = Path(raw)
            destination = run_dir / "manifest.json"
            destination.write_text('{"previous": true}\n')
            replacement = {"totals": {"records": 3}, "errors": []}

            def observe_replace(staged, target):
                self.assertEqual(json.loads(target.read_text()), {"previous": True})
                self.assertEqual(json.loads(staged.read_text()), replacement)
                return original_replace(staged, target)

            with mock.patch.object(Path, "replace", side_effect=observe_replace, autospec=True) as replace:
                validate_run_cli._write_manifest(run_dir, replacement)
            replace.assert_called_once()
            self.assertEqual(json.loads(destination.read_text()), replacement)
            self.assertEqual(list(run_dir.iterdir()), [destination])


if __name__ == "__main__":
    unittest.main()
