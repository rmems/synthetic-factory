#!/usr/bin/env python3
"""Regression tests for the Grok 4.6 Hub snapshot publisher."""

import hashlib
import json
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
            outside_batch = root / "outside.jsonl"
            outside_batch.write_text('{"id":"not-a-factory-batch"}\n')
            outside_notes = root / "outside.md"
            outside_notes.write_text("not factory notes\n")
            (source / "batch-r03.jsonl").symlink_to(outside_batch)
            (source / "NOTES-r02b.md").symlink_to(outside_notes)

            with mock.patch.object(publisher, "FACTORY_ROOT", root / "raw"), mock.patch.object(
                publisher, "HF_ROOT", destination_root
            ):
                stats = publisher.snapshot_one(ITEM)
                copied = destination_root / ITEM["hub"] / "data" / "raw" / last.name
                card = (destination_root / ITEM["hub"] / "README.md").read_text()

                self.assertEqual(stats["last"], "r02b")
                self.assertIn("batch-r01.jsonl` through `data/raw/batch-r02b.jsonl", card)
                self.assertNotEqual(copied.stat().st_ino, last.stat().st_ino)
                self.assertFalse(
                    (destination_root / ITEM["hub"] / "data" / "raw" / "batch-r03.jsonl").exists()
                )
                self.assertFalse(
                    (destination_root / ITEM["hub"] / "data" / "metadata" / "NOTES-r02b.md").exists()
                )
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
            committed_batch = source / "batch-r03.jsonl"
            committed_batch.write_text('{"id":"committed"}\n')
            committed_notes = source / "NOTES-r03.md"
            committed_notes.write_text("committed\n")
            (source / "ROUND-r03.complete.json").write_text(
                json.dumps(
                    {
                        "factory": ITEM["slug"],
                        "round": 3,
                        "commit_point": "ROUND-r03.complete.json",
                        "files": [
                            {
                                "name": "batch-r03.jsonl",
                                "sha256": hashlib.sha256(
                                    committed_batch.read_bytes()
                                ).hexdigest(),
                            },
                            {
                                "name": "NOTES-r03.md",
                                "sha256": hashlib.sha256(
                                    committed_notes.read_bytes()
                                ).hexdigest(),
                            },
                        ],
                    }
                )
                + "\n"
            )
            (source / "NOTES-r01.md").write_text("legacy\n")
            (source / "NOTES-r02.md").write_text("uncommitted\n")

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

                committed_notes.write_text("tampered\n")
                with self.assertRaisesRegex(SystemExit, "hash mismatch"):
                    publisher.snapshot_one(ITEM)

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

    def test_snapshot_keeps_legacy_named_marker_baseline_payload(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "raw" / ITEM["slug"]
            source.mkdir(parents=True)
            (source / ".round-marker-mode.json").write_text(
                '{"version":1,"legacy_baseline":1}\n'
            )
            legacy = source / "episodes.jsonl"
            legacy.write_text('{"id":"legacy-episode"}\n')
            (source / "NOTES-r01.md").write_text("legacy notes\n")

            self.assertEqual([path.name for path in publisher.published_batches(source)], ["episodes.jsonl"])
            with mock.patch.object(publisher, "FACTORY_ROOT", root / "raw"), mock.patch.object(
                publisher, "HF_ROOT", root / "hf"
            ):
                stats = publisher.snapshot_one(ITEM)

            raw = root / "hf" / ITEM["hub"] / "data" / "raw"
            meta = root / "hf" / ITEM["hub"] / "data" / "metadata"
            card = (root / "hf" / ITEM["hub"] / "README.md").read_text()
            self.assertEqual(stats["records"], 1)
            self.assertTrue((raw / legacy.name).is_file())
            self.assertTrue((meta / "NOTES-r01.md").is_file())
            self.assertIn("data/raw/episodes.jsonl", card)

    def test_snapshot_refuses_untrusted_completion_manifests(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / ITEM["slug"]
            source.mkdir()
            (source / ".round-marker-mode.json").write_text(
                '{"version":1,"legacy_baseline":0}\n'
            )
            batch = source / "batch-r01.jsonl"
            batch.write_text('{"id":"committed"}\n')
            marker = source / "ROUND-r01.complete.json"

            for manifest, message in (
                (
                    {
                        "factory": "other-factory",
                        "round": 1,
                        "commit_point": marker.name,
                        "files": [],
                    },
                    "identity mismatch",
                ),
                (
                    {
                        "factory": ITEM["slug"],
                        "round": 1,
                        "commit_point": marker.name,
                        "files": [{"name": batch.name, "sha256": "0" * 64}],
                    },
                    "hash mismatch",
                ),
            ):
                with self.subTest(message=message):
                    marker.write_text(json.dumps(manifest) + "\n")
                    with self.assertRaisesRegex(SystemExit, message):
                        publisher.published_batches(source)

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

    def test_targeted_snapshot_preserves_full_inventory(self):
        other = {**ITEM, "slug": "other-factory", "hub": "other"}
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for item, record_id in ((ITEM, "selected"), (other, "other")):
                source = root / "raw" / item["slug"]
                source.mkdir(parents=True)
                (source / "batch-r01.jsonl").write_text(
                    json.dumps({"id": record_id}) + "\n"
                )
            with mock.patch.object(publisher, "FACTORY_ROOT", root / "raw"), mock.patch.object(
                publisher, "HF_ROOT", root / "hf"
            ), mock.patch.object(publisher, "factories", return_value=[ITEM, other]):
                publisher.cmd_snapshot()
                publisher.cmd_snapshot(ITEM["hub"])

            inventory = (root / "hf" / "SYNTHETIC-DATA-FACTORY-GROK46.md").read_text()
            self.assertIn(f"`{ITEM['hub']}/`", inventory)
            self.assertIn(f"`{other['hub']}/`", inventory)

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

    def test_direct_create_and_collect_honor_only(self):
        whoami = SimpleNamespace(returncode=0, stdout='{"user":"rmems"}', stderr="")
        with mock.patch.object(publisher.subprocess, "run", return_value=whoami), mock.patch.object(
            publisher, "cmd_create"
        ) as create, mock.patch.object(publisher, "cmd_collect") as collect, mock.patch.object(
            sys, "argv", ["publish_grok46_hub.py", "create", "--only", ITEM["hub"]]
        ):
            self.assertEqual(publisher.main(), 0)
        create.assert_called_once_with(ITEM["hub"])
        collect.assert_not_called()

        with mock.patch.object(publisher.subprocess, "run", return_value=whoami), mock.patch.object(
            publisher, "cmd_create"
        ) as create, mock.patch.object(publisher, "cmd_collect") as collect, mock.patch.object(
            sys, "argv", ["publish_grok46_hub.py", "collect", "--only", ITEM["slug"]]
        ):
            self.assertEqual(publisher.main(), 0)
        create.assert_not_called()
        collect.assert_called_once_with(ITEM["slug"])


if __name__ == "__main__":
    unittest.main()
