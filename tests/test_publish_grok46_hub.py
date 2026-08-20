#!/usr/bin/env python3
"""Regression tests for the Grok 4.6 Hub snapshot publisher."""

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import publish_grok46_hub as publisher  # noqa: E402


ITEM = {
    "slug": "long-horizon-coding-factory",
    "hub": "long-horizon-coding-trajectories",
    "pretty": "Long Horizon Coding Trajectories",
    "blurb": "Test factory.",
    "tags": ["synthetic-data"],
}


class PublishGrok46HubTests(unittest.TestCase):
    def test_snapshot_uses_independent_copies_and_truthful_lettered_range(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "raw" / ITEM["slug"]
            destination_root = root / "hf"
            source.mkdir(parents=True)
            first = source / "batch-r01.jsonl"
            last = source / "batch-r02b.jsonl"
            first.write_text('{"id":"first"}\n')
            last.write_text('{"id":"last"}\n')
            (source / "NOTES-r01.md").write_text("Novel coverage: 80%\n")

            with mock.patch.object(publisher, "FACTORY_ROOT", root / "raw"), mock.patch.object(
                publisher, "HF_ROOT", destination_root
            ):
                stats = publisher.snapshot_one(ITEM)
                copied = destination_root / ITEM["hub"] / "data" / "raw" / last.name
                card = (destination_root / ITEM["hub"] / "README.md").read_text()

                self.assertEqual(stats["last"], "r02b")
                self.assertIn("batch-r01.jsonl` through `data/raw/batch-r02b.jsonl", card)
                self.assertNotEqual(copied.stat().st_ino, last.stat().st_ino)
                copied.write_text('{"id":"changed"}\n')
                self.assertEqual(last.read_text(), '{"id":"last"}\n')

                stale = root / "stale.jsonl"
                stale.write_text("stale\n")
                copied.unlink()
                copied.symlink_to(stale)
                publisher.snapshot_one(ITEM)
                self.assertFalse(copied.is_symlink())
                self.assertEqual(copied.read_text(), last.read_text())

    def test_snapshot_keeps_legacy_baseline_and_filters_uncommitted_marker_batches(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "raw" / ITEM["slug"]
            destination_root = root / "hf"
            source.mkdir(parents=True)
            (source / ".round-marker-mode.json").write_text(
                '{"version":1,"legacy_baseline":1}\n'
            )
            (source / "batch-r01.jsonl").write_text('{"id":"legacy"}\n')
            (source / "batch-r02.jsonl").write_text('{"id":"uncommitted"}\n')
            (source / "batch-r03.jsonl").write_text('{"id":"committed"}\n')
            (source / "ROUND-r03.complete.json").write_text('{"round":3}\n')
            (source / "NOTES-r01.md").write_text("legacy\n")
            (source / "NOTES-r02.md").write_text("uncommitted\n")
            (source / "NOTES-r03.md").write_text("committed\n")

            self.assertEqual(
                [path.name for path in publisher.published_batches(source)],
                ["batch-r01.jsonl", "batch-r03.jsonl"],
            )
            stale_destination = (
                destination_root / ITEM["hub"] / "data" / "raw" / "batch-r02.jsonl"
            )
            stale_destination.parent.mkdir(parents=True)
            stale_destination.write_text('{"id":"stale"}\n')
            stale_note = destination_root / ITEM["hub"] / "data" / "metadata" / "NOTES-r02.md"
            stale_note.parent.mkdir(parents=True)
            stale_note.write_text("stale\n")
            with mock.patch.object(publisher, "FACTORY_ROOT", root / "raw"), mock.patch.object(
                publisher, "HF_ROOT", destination_root
            ):
                publisher.snapshot_one(ITEM)
                raw = destination_root / ITEM["hub"] / "data" / "raw"
                self.assertTrue((raw / "batch-r01.jsonl").is_file())
                self.assertFalse((raw / "batch-r02.jsonl").exists())
                self.assertTrue((raw / "batch-r03.jsonl").is_file())
                meta = destination_root / ITEM["hub"] / "data" / "metadata"
                self.assertTrue((meta / "NOTES-r01.md").is_file())
                self.assertFalse((meta / "NOTES-r02.md").exists())
                self.assertTrue((meta / "NOTES-r03.md").is_file())

            empty_source = root / "raw" / "empty-factory"
            empty_source.mkdir()
            empty_item = {**ITEM, "slug": "empty-factory", "hub": "empty"}
            with mock.patch.object(publisher, "FACTORY_ROOT", root / "raw"), mock.patch.object(
                publisher, "HF_ROOT", destination_root
            ):
                publisher.snapshot_one(empty_item)
                card = (destination_root / "empty" / "README.md").read_text()
            self.assertIn("contains no published raw batch files", card)
            self.assertNotIn("batch-r01.jsonl` through", card)

    def test_only_limits_create_and_collection_operations(self):
        other = {**ITEM, "slug": "other-factory", "hub": "other"}
        with mock.patch.object(publisher, "factories", return_value=[ITEM, other]), mock.patch.object(
            publisher, "run"
        ) as run:
            publisher.cmd_create(ITEM["hub"])
            publisher.cmd_collect(ITEM["slug"])

        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(len(commands), 2)
        self.assertTrue(
            all(any(ITEM["hub"] in token for token in command) for command in commands)
        )

    def test_all_only_scopes_payload_not_complete_collection_maintenance(self):
        whoami = SimpleNamespace(returncode=0, stdout='{"user":"rmems"}', stderr="")
        with mock.patch.object(publisher.subprocess, "run", return_value=whoami), mock.patch.object(
            publisher, "cmd_snapshot"
        ) as snapshot, mock.patch.object(publisher, "cmd_create") as create, mock.patch.object(
            publisher, "cmd_upload"
        ) as upload, mock.patch.object(publisher, "cmd_collect") as collect, mock.patch.object(
            sys, "argv", ["publish_grok46_hub.py", "all", "--only", ITEM["hub"]]
        ):
            self.assertEqual(publisher.main(), 0)

        snapshot.assert_called_once_with(ITEM["hub"])
        upload.assert_called_once_with(ITEM["hub"])
        create.assert_called_once_with()
        collect.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
