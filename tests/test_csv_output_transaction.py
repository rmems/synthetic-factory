"""Output failures cannot strand a partial CSV replay destination."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pipelines.csv_mill import generate, generate_io
from pipelines.csv_mill._contract import CsvRefusal
from tests.test_csv import FIXTURE


class CsvOutputTransaction(unittest.TestCase):
    def test_generation_failure_does_not_create_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "run"
            with patch.object(generate, "fail_episode", side_effect=ValueError("injected")):
                request = generate.GenerateRequest(FIXTURE, dest, all_plants=True)
                with self.assertRaisesRegex(ValueError, "injected"):
                    generate.run(request)
            self.assertEqual(list(Path(temp).iterdir()), [])
            generate.run(generate.GenerateRequest(FIXTURE, dest, all_plants=True))

    def test_each_write_failure_cleans_staging_and_allows_retry(self):
        original = generate_io._OwnedStage.write
        for filename in ("records.jsonl", "NOTES.md", "RUN.json"):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as temp:
                dest = Path(temp) / "run"

                def write(stage, name, payload, failing_name=filename):
                    original(stage, name, payload)
                    if name == failing_name:
                        raise OSError("injected disk failure")

                with patch.object(generate_io._OwnedStage, "write", write):
                    request = generate.GenerateRequest(FIXTURE, dest, all_plants=True)
                    with self.assertRaisesRegex(CsvRefusal, "injected disk failure"):
                        generate.run(request)
                self.assertEqual(list(Path(temp).iterdir()), [])
                generate.run(generate.GenerateRequest(FIXTURE, dest, all_plants=True))
                self.assertEqual(len(list(dest.iterdir())), 3)

    def test_dangling_destination_symlink_is_coded_refusal(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "run"
            dest.symlink_to("missing")
            request = generate.GenerateRequest(FIXTURE, dest, all_plants=True)
            with self.assertRaises(CsvRefusal) as caught:
                generate.run(request)
            self.assertEqual(caught.exception.code, "DESTINATION_EXISTS")
            self.assertEqual(dest.readlink(), Path("missing"))

    def test_destination_created_during_writes_is_not_replaced(self):
        original = generate_io._publish
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "run"

            def publish(parent, staged, destination, descriptor):
                destination.mkdir()
                original(parent, staged, destination, descriptor)

            with patch.object(generate_io, "_publish", publish):
                request = generate.GenerateRequest(FIXTURE, dest, all_plants=True)
                with self.assertRaises(CsvRefusal) as caught:
                    generate.run(request)
            self.assertEqual(caught.exception.code, "DESTINATION_EXISTS")
            self.assertEqual(list(dest.iterdir()), [])
            self.assertEqual(list(Path(temp).iterdir()), [dest])

    def test_publish_failure_cleans_private_stage(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "run"
            with patch.object(generate_io, "rename_noreplace", side_effect=OSError("injected")):
                request = generate.GenerateRequest(FIXTURE, dest, all_plants=True)
                with self.assertRaisesRegex(CsvRefusal, "injected"):
                    generate.run(request)
            self.assertEqual(list(Path(temp).iterdir()), [])
