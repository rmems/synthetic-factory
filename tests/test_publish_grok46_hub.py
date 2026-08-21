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
    def test_factory_discovery_and_snapshot_reject_symlinked_factory_roots(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw = root / "raw"
            raw.mkdir()
            outside = root / "outside-factory"
            outside.mkdir()
            (raw / ITEM["slug"]).symlink_to(outside, target_is_directory=True)

            with mock.patch.object(publisher, "FACTORY_ROOT", raw):
                with self.assertRaisesRegex(SystemExit, "unsafe factory directory"):
                    publisher.factories()
                with self.assertRaisesRegex(SystemExit, "unsafe factory directory"):
                    publisher.snapshot_one(ITEM)

            linked_root = root / "linked-raw"
            linked_root.symlink_to(raw, target_is_directory=True)
            with mock.patch.object(publisher, "FACTORY_ROOT", linked_root):
                with self.assertRaisesRegex(SystemExit, "unsafe factory root"):
                    publisher.factories()

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

            empty = {**ITEM, "slug": "empty-factory", "hub": "empty"}
            (root / "raw" / empty["slug"]).mkdir()
            with mock.patch.object(publisher, "FACTORY_ROOT", root / "raw"), mock.patch.object(
                publisher, "HF_ROOT", destination_root
            ):
                publisher.snapshot_one(empty)
            empty_card = (destination_root / empty["hub"] / "README.md").read_text()
            self.assertIn("payload. The factory source tree is\n`outputs/raw/", empty_card)

    def test_snapshot_keeps_legacy_baseline_and_filters_uncommitted_marker_batches(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "raw" / ITEM["slug"]
            destination_root = root / "hf"
            source.mkdir(parents=True)
            (source / ".round-marker-mode.json").write_text(
                '{"version":1,"legacy_baseline":1,"commit_point":"ROUND-rNN.complete.json"}\n'
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

    def test_snapshot_refuses_symlinked_payload_directories(self):
        for leaf in ("raw", "metadata"):
            with self.subTest(leaf=leaf), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                source = root / "raw" / ITEM["slug"]
                source.mkdir(parents=True)
                (source / "batch-r01.jsonl").write_text('{"id":"source"}\n')
                outside = root / "outside"
                outside.mkdir()
                unsafe = root / "hf" / ITEM["hub"] / "data" / leaf
                unsafe.parent.mkdir(parents=True)
                unsafe.symlink_to(outside, target_is_directory=True)

                with mock.patch.object(publisher, "FACTORY_ROOT", root / "raw"), mock.patch.object(
                    publisher, "HF_ROOT", root / "hf"
                ):
                    with self.assertRaisesRegex(SystemExit, "unsafe snapshot directory"):
                        publisher.snapshot_one(ITEM)

                self.assertEqual(list(outside.iterdir()), [])

    def test_snapshot_replaces_symlinked_metadata_files(self):
        for name in ("README.md", "LICENSE", "ATTRIBUTION.md"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                source = root / "raw" / ITEM["slug"]
                source.mkdir(parents=True)
                (source / "batch-r01.jsonl").write_text('{"id":"source"}\n')
                destination = root / "hf" / ITEM["hub"]
                destination.mkdir(parents=True)
                outside = root / "outside.txt"
                outside.write_text("must not change\n")
                endpoint = destination / name
                endpoint.symlink_to(outside)

                with mock.patch.object(publisher, "FACTORY_ROOT", root / "raw"), mock.patch.object(
                    publisher, "HF_ROOT", root / "hf"
                ):
                    publisher.snapshot_one(ITEM)

                self.assertFalse(endpoint.is_symlink())
                self.assertEqual(outside.read_text(), "must not change\n")

    def test_snapshot_keeps_legacy_named_marker_baseline_payload(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "raw" / ITEM["slug"]
            source.mkdir(parents=True)
            (source / ".round-marker-mode.json").write_text(
                '{"version":1,"legacy_baseline":1,"commit_point":"ROUND-rNN.complete.json"}\n'
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

            other = {**ITEM, "slug": "other-factory", "hub": "other"}
            other_source = root / "raw" / other["slug"]
            other_source.mkdir()
            (other_source / "batch-r01.jsonl").write_text('{"id":"other"}\n')
            with mock.patch.object(publisher, "FACTORY_ROOT", root / "raw"), mock.patch.object(
                publisher, "HF_ROOT", root / "hf"
            ), mock.patch.object(publisher, "factories", return_value=[ITEM, other]):
                publisher.cmd_snapshot(other["hub"])
                local = publisher.local_snapshot_stats(ITEM)

            inventory = (root / "hf" / "SYNTHETIC-DATA-FACTORY-GROK46.md").read_text()
            self.assertEqual(local["records"], 1)
            self.assertIsNone(local["last"])
            self.assertIn(f"| `{ITEM['hub']}/`", inventory)
            self.assertIn(f"| `{other['hub']}/`", inventory)
            self.assertIn(f"| `{other['hub']}/` |", inventory)
            self.assertIn(f"| `{other['slug']}` | 1 | 1 |", inventory)

    def test_snapshot_refuses_untrusted_completion_manifests(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / ITEM["slug"]
            source.mkdir()
            (source / ".round-marker-mode.json").write_text(
                '{"version":1,"legacy_baseline":0,"commit_point":"ROUND-rNN.complete.json"}\n'
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
                        "commit_point": "ROUND-r02.complete.json",
                        "files": [{"name": batch.name, "sha256": "0" * 64}],
                    },
                    "commit point mismatch",
                ),
                (
                    {
                        "factory": ITEM["slug"],
                        "round": 1,
                        "commit_point": marker.name,
                        "files": [],
                    },
                    "no unique file entry",
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

    def test_snapshot_refuses_manifest_without_a_regular_batch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "raw" / ITEM["slug"]
            source.mkdir(parents=True)
            (source / ".round-marker-mode.json").write_text(
                '{"version":1,"legacy_baseline":0,"commit_point":"ROUND-rNN.complete.json"}\n'
            )
            marker = source / "ROUND-r01.complete.json"
            marker.write_text(
                json.dumps(
                    {
                        "factory": source.name,
                        "round": 1,
                        "commit_point": marker.name,
                        "files": [
                            {"name": "batch-r01.jsonl", "sha256": "0" * 64}
                        ],
                    }
                )
                + "\n"
            )
            stale = root / "hf" / ITEM["hub"] / "data" / "raw" / "batch-r01.jsonl"
            stale.parent.mkdir(parents=True)
            stale.write_text('{"id":"preserve"}\n')

            with mock.patch.object(publisher, "FACTORY_ROOT", root / "raw"), mock.patch.object(
                publisher, "HF_ROOT", root / "hf"
            ):
                with self.assertRaisesRegex(SystemExit, "no regular batch"):
                    publisher.snapshot_one(ITEM)

            self.assertEqual(stale.read_text(), '{"id":"preserve"}\n')

    def test_snapshot_refuses_manifest_without_a_regular_notes_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "raw" / ITEM["slug"]
            source.mkdir(parents=True)
            (source / ".round-marker-mode.json").write_text(
                '{"version":1,"legacy_baseline":0,"commit_point":"ROUND-rNN.complete.json"}\n'
            )
            batch = source / "batch-r01.jsonl"
            batch.write_text('{"id":"committed"}\n')
            notes = source / "NOTES-r01.md"
            notes.write_text("Novel coverage: 80%\n")
            marker = source / "ROUND-r01.complete.json"
            marker.write_text(
                json.dumps(
                    {
                        "factory": source.name,
                        "round": 1,
                        "commit_point": marker.name,
                        "files": [
                            {"name": batch.name, "sha256": hashlib.sha256(batch.read_bytes()).hexdigest()},
                            {"name": notes.name, "sha256": hashlib.sha256(notes.read_bytes()).hexdigest()},
                        ],
                    }
                )
                + "\n"
            )
            notes.unlink()
            stale = root / "hf" / ITEM["hub"] / "data" / "metadata" / notes.name
            stale.parent.mkdir(parents=True)
            stale.write_text("preserve\n")

            with mock.patch.object(publisher, "FACTORY_ROOT", root / "raw"), mock.patch.object(
                publisher, "HF_ROOT", root / "hf"
            ):
                with self.assertRaisesRegex(SystemExit, "no regular notes"):
                    publisher.snapshot_one(ITEM)

            self.assertEqual(stale.read_text(), "preserve\n")

    def test_snapshot_validates_every_declared_manifest_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / ITEM["slug"]
            source.mkdir()
            (source / ".round-marker-mode.json").write_text(
                '{"version":1,"legacy_baseline":0,"commit_point":"ROUND-rNN.complete.json"}\n'
            )
            batch = source / "batch-r01.jsonl"
            notes = source / "NOTES-r01.md"
            evidence = source / "EVIDENCE-r01.json"
            batch.write_text('{"id":"committed"}\n')
            notes.write_text("Novel coverage: 80%\n")
            evidence.write_text('{"result":"passed"}\n')
            marker = source / "ROUND-r01.complete.json"
            marker.write_text(
                json.dumps(
                    {
                        "factory": source.name,
                        "round": 1,
                        "commit_point": marker.name,
                        "files": [
                            {"name": batch.name, "sha256": hashlib.sha256(batch.read_bytes()).hexdigest()},
                            {"name": notes.name, "sha256": hashlib.sha256(notes.read_bytes()).hexdigest()},
                            {"name": evidence.name, "sha256": hashlib.sha256(evidence.read_bytes()).hexdigest()},
                        ],
                    }
                )
                + "\n"
            )

            self.assertEqual([path.name for path in publisher.published_batches(source)], [batch.name])
            evidence.write_text('{"result":"tampered"}\n')
            with self.assertRaisesRegex(SystemExit, "hash mismatch"):
                publisher.published_batches(source)

    def test_snapshot_replaces_symlinked_shared_inventory(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "raw" / ITEM["slug"]
            source.mkdir(parents=True)
            (source / "batch-r01.jsonl").write_text('{"id":"source"}\n')
            inventory = root / "hf" / "SYNTHETIC-DATA-FACTORY-GROK46.md"
            inventory.parent.mkdir()
            outside = root / "outside.txt"
            outside.write_text("must not change\n")
            inventory.symlink_to(outside)

            with mock.patch.object(publisher, "FACTORY_ROOT", root / "raw"), mock.patch.object(
                publisher, "HF_ROOT", root / "hf"
            ), mock.patch.object(publisher, "factories", return_value=[ITEM]):
                publisher.cmd_snapshot()

            self.assertFalse(inventory.is_symlink())
            self.assertEqual(outside.read_text(), "must not change\n")

    def test_marker_mode_rejects_unsafe_mode_entries(self):
        for kind in ("directory", "dangling_symlink"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                source = Path(td) / ITEM["slug"]
                source.mkdir()
                (source / "batch-r01.jsonl").write_text('{"id":"uncommitted"}\n')
                mode = source / ".round-marker-mode.json"
                if kind == "directory":
                    mode.mkdir()
                else:
                    mode.symlink_to(source / "missing-marker-mode.json")

                with self.assertRaisesRegex(SystemExit, "unsafe marker mode file"):
                    publisher.published_batches(source)

    def test_marker_mode_rejects_incomplete_or_unbacked_schema(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / ITEM["slug"]
            source.mkdir()
            (source / "episodes.jsonl").write_text('{"id":"legacy"}\n')
            mode = source / ".round-marker-mode.json"

            for payload, message in (
                (
                    {"version": 2, "legacy_baseline": 0, "commit_point": "ROUND-rNN.complete.json"},
                    "version",
                ),
                (
                    {"version": 1, "legacy_baseline": 0, "commit_point": "ROUND-rNN.publishing.json"},
                    "commit point",
                ),
                (
                    {"version": 1, "legacy_baseline": 26, "commit_point": "ROUND-rNN.complete.json"},
                    "exceeds discovered",
                ),
                (
                    {"version": 1, "legacy_baseline": 0, "commit_point": "ROUND-rNN.complete.json"},
                    "excludes legacy r01",
                ),
            ):
                with self.subTest(message=message):
                    mode.write_text(json.dumps(payload) + "\n")
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

    def test_upload_syncs_managed_payload_and_note_paths(self):
        with mock.patch.object(publisher, "factories", return_value=[ITEM]), mock.patch.object(
            publisher, "run"
        ) as run:
            publisher.cmd_upload()

        command = run.call_args.args[0]
        self.assertIn("--delete", command)
        self.assertEqual(
            [command[index + 1] for index, value in enumerate(command) if value == "--delete"],
            ["data/raw/*", "data/metadata/NOTES-r*.md"],
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
            self.assertIn(f"| `{other['slug']}` | 1 | 1 |", inventory)

    def test_all_only_scopes_payload_not_complete_collection_maintenance(self):
        whoami = SimpleNamespace(returncode=0, stdout='{"user":"rmems"}', stderr="")
        with mock.patch.object(publisher, "factories", return_value=[ITEM]), mock.patch.object(
            publisher.subprocess, "run", return_value=whoami
        ), mock.patch.object(
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
        with mock.patch.object(publisher, "factories", return_value=[ITEM]), mock.patch.object(
            publisher.subprocess, "run", return_value=whoami
        ), mock.patch.object(
            publisher, "cmd_create"
        ) as create, mock.patch.object(publisher, "cmd_collect") as collect, mock.patch.object(
            sys, "argv", ["publish_grok46_hub.py", "create", "--only", ITEM["hub"]]
        ):
            self.assertEqual(publisher.main(), 0)
        create.assert_called_once_with(ITEM["hub"])
        collect.assert_not_called()

        with mock.patch.object(publisher, "factories", return_value=[ITEM]), mock.patch.object(
            publisher.subprocess, "run", return_value=whoami
        ), mock.patch.object(
            publisher, "cmd_create"
        ) as create, mock.patch.object(publisher, "cmd_collect") as collect, mock.patch.object(
            sys, "argv", ["publish_grok46_hub.py", "collect", "--only", ITEM["slug"]]
        ):
            self.assertEqual(publisher.main(), 0)
        create.assert_not_called()
        collect.assert_called_once_with(ITEM["slug"])

    def test_unknown_only_target_fails_before_hub_authentication(self):
        with mock.patch.object(publisher, "factories", return_value=[ITEM]), mock.patch.object(
            publisher.subprocess, "run"
        ) as whoami, mock.patch.object(
            sys, "argv", ["publish_grok46_hub.py", "snapshot", "--only", "typo"]
        ):
            self.assertEqual(publisher.main(), 2)

        whoami.assert_not_called()


if __name__ == "__main__":
    unittest.main()
