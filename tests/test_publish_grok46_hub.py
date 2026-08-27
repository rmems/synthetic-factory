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


def valid_legacy_episode(record_id, round_number=1, success=True):
    alternate_scenario = str(record_id).endswith("-1")
    steps = [
        {
            "n": index,
            "decision_basis": "Observation: inspect the timezone failure",
            "tool_call": {"name": "bash", "args": {"command": f"echo {index}"}},
            "observation": f"inspected step {index}",
        }
        for index in range(1, 19)
    ]
    steps[2]["tool_call"]["args"]["command"] = "apply patch to converter"
    steps[2]["observation"] = "edited the converter"
    steps[3]["tool_call"]["args"]["command"] = "pytest timezone"
    steps[3]["observation"] = "test failed with DST error"
    steps[4]["tool_call"]["args"]["command"] = "sed read converter"
    steps[4]["observation"] = "re-read the failing branch"
    steps[5]["tool_call"]["args"]["command"] = "apply patch to fix DST fold"
    steps[5]["observation"] = "fixed the branch"
    steps[6]["tool_call"]["args"]["command"] = "pytest timezone"
    steps[6]["observation"] = "tests passed; fix verified"
    return {
        "id": record_id,
        "goal": "repair a deterministic fixture",
        "codebase_type": "rust-cli" if alternate_scenario else "python-service",
        "bug_class": "parser-boundary" if alternate_scenario else "timezone-conversion",
        "steps": steps,
        "outcome": "fixture repaired" if success else "fixture mitigated and handed off",
        "reward": {"success": success},
        "meta": {
            "factory": ITEM["slug"],
            "round": round_number,
            "generator": "grok-4.6",
        },
    }


def write_valid_legacy(path, count=2):
    match = publisher.BATCH_NAME_RE.fullmatch(path.name)
    round_number = int(match.group(1)) if match is not None else 1
    path.write_text(
        "".join(
            json.dumps(
                valid_legacy_episode(
                    f"{path.stem}-{index}",
                    round_number=round_number,
                    success=index % 2 == 0,
                )
            )
            + "\n"
            for index in range(count)
        )
    )
    (path.parent / f"NOTES-r{round_number:02d}.md").write_text(
        "Novel coverage: 80%\n"
    )


def write_valid_thalamic(path, record_id):
    path.write_text(
        json.dumps(
            {
                "id": record_id,
                "state": {"sim_or_real": "designed"},
                "proposed_action": {"action": "noop", "decision_basis": "fixture"},
                "safety_decision": {
                    "decision": "ACCEPT",
                    "rationale": "bounded fixture",
                },
                "executed_action": {"action": "noop"},
                "future_outcome": {"success": True},
                "reward_components": {"total": 0.0},
                "meta": {"round": 1},
            }
        )
        + "\n"
    )


def write_valid_completed_long_horizon(path, round_number):
    def steps():
        values = [
            {
                "n": index,
                "decision_basis": "Observation: inspect the timezone failure",
                "tool_call": {"name": "bash", "args": {"command": f"echo {index}"}},
                "observation": f"inspected step {index}",
            }
            for index in range(1, 19)
        ]
        values[2]["tool_call"]["args"]["command"] = "apply patch to converter"
        values[2]["observation"] = "edited the converter"
        values[3]["tool_call"]["args"]["command"] = "pytest timezone"
        values[3]["observation"] = "test failed with DST error"
        values[4]["tool_call"]["args"]["command"] = "sed read converter"
        values[4]["observation"] = "re-read the failing branch"
        values[5]["tool_call"]["args"]["command"] = "apply patch to fix DST fold"
        values[5]["observation"] = "fixed the branch"
        values[6]["tool_call"]["args"]["command"] = "pytest timezone"
        values[6]["observation"] = "tests passed; fix verified"
        return values

    records = []
    for index, success in enumerate((True, False)):
        records.append(
            {
                "id": f"committed-r{round_number:02d}-{index}",
                "goal": "repair timezone conversion",
                "codebase_type": "rust-cli" if index else "python-service",
                "bug_class": "parser-boundary" if index else "timezone-conversion",
                "steps": steps(),
                "outcome": "fixed" if success else "mitigated and handed off",
                "reward": {"success": success},
                "meta": {
                    "factory": ITEM["slug"],
                    "round": round_number,
                    "generator": "grok-4.6",
                },
            }
        )
    path.write_text("".join(json.dumps(record) + "\n" for record in records))


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
            write_valid_legacy(first)
            write_valid_legacy(last)
            original_last = last.read_text()
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
                copied = destination_root / publisher.HF_DATASETS_DIRNAME / ITEM["hub"] / "data" / "raw" / last.name
                card = (destination_root / publisher.HF_DATASETS_DIRNAME / ITEM["hub"] / "README.md").read_text()

                self.assertEqual(stats["last"], "r02b")
                self.assertIn("batch-r01.jsonl` through `data/raw/batch-r02b.jsonl", card)
                self.assertNotEqual(copied.stat().st_ino, last.stat().st_ino)
                self.assertFalse(
                    (destination_root / publisher.HF_DATASETS_DIRNAME / ITEM["hub"] / "data" / "raw" / "batch-r03.jsonl").exists()
                )
                self.assertFalse(
                    (destination_root / publisher.HF_DATASETS_DIRNAME / ITEM["hub"] / "data" / "metadata" / "NOTES-r02b.md").exists()
                )
                self.assertTrue(
                    (destination_root / publisher.HF_DATASETS_DIRNAME / ITEM["hub"] / "data" / "metadata" / "NOTES-r02.md").is_file()
                )
                copied.write_text('{"id":"changed"}\n')
                self.assertEqual(last.read_text(), original_last)

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
            empty_card = (destination_root / publisher.HF_DATASETS_DIRNAME / empty["hub"] / "README.md").read_text()
            self.assertIn("payload. The factory source tree is\n`outputs/raw/", empty_card)

    def test_snapshot_card_preserves_noncanonical_batch_names(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "raw" / ITEM["slug"]
            source.mkdir(parents=True)
            write_valid_legacy(source / "batch-r1a.jsonl")

            with mock.patch.object(publisher, "FACTORY_ROOT", root / "raw"), mock.patch.object(
                publisher, "HF_ROOT", root / "hf"
            ):
                publisher.snapshot_one(ITEM)

            card = (root / "hf" / publisher.HF_DATASETS_DIRNAME / ITEM["hub"] / "README.md").read_text()
            self.assertIn("`data/raw/batch-r1a.jsonl`", card)
            self.assertNotIn("`data/raw/batch-r01a.jsonl`", card)
            self.assertNotIn("## Factory-mix quarantine", card)

    def test_snapshot_card_discloses_issue_43_factory_mix(self):
        item = {
            "slug": "email-webhook-retry-factory",
            "hub": "email-webhook-retry-trajectories",
            "pretty": "Email Webhook Retry Trajectories",
            "blurb": "Test factory.",
            "tags": ["synthetic-data"],
        }
        card = publisher.render_card(
            item,
            records=100,
            bytes_=4096,
            first="r56",
            last="r58",
            payload_names=["batch-r56.jsonl", "batch-r57.jsonl", "batch-r58.jsonl"],
        )
        self.assertIn("## Factory-mix quarantine", card)
        self.assertIn("**94**, not 100", card)
        self.assertIn("`sir-r56-meili-swap-leftover3c-rebuild`", card)

    def test_preference_pair_cards_disclose_the_trajectory_schema(self):
        # The two published Grok preference repos are trajectory DPO, not Fable
        # same-state pairs; the card must say so and claim no FFPC purity.
        for slug in ("code-review-preference-factory", "tool-use-preference-factory"):
            hub = publisher.hub_name(slug)
            card = publisher.render_card(
                {**ITEM, "slug": slug, "hub": hub},
                records=3,
                bytes_=4096,
                first="r01",
                last="r02",
            )

            self.assertTrue(hub.endswith("-preference-pairs"), hub)
            self.assertIn("## Record schema", card)
            self.assertIn("trajectory preference pair", card)
            self.assertIn("`proposed_action` field", card)
            self.assertIn("curate_trajectory_preferences.py", card)
            self.assertIn("no FFPC-equivalent same-state", card)
            self.assertIn("payload is unfiltered", card)
            # The YAML tag block must still be the first --- delimited section.
            self.assertEqual(len(card.split("---", 2)), 3)

    def test_code_review_card_discloses_leftover_episode_lines(self):
        kind_mix = [
            SimpleNamespace(
                record_id=f"leftover-{index}",
                source_name="batch-r723.jsonl",
                source_line=index + 1,
                record_kind="episode",
                source_sha256=f"{index:064x}",
            )
            for index in range(12)
        ]
        card = publisher.render_card(
            {
                **ITEM,
                "slug": "code-review-preference-factory",
                "hub": "code-review-preference-pairs",
            },
            records=2976,
            bytes_=4096,
            first="r01",
            last="r02",
            kind_mix=kind_mix,
        )

        self.assertIn("2,964 trajectory", card)
        self.assertIn("12 quarantined\nleftover-mill episode records", card)
        self.assertIn("without `chosen` / `rejected`\nobjects", card)
        self.assertNotIn("Each line is a **trajectory preference pair**", card)

    def test_trajectory_cards_omit_the_preference_pair_disclosure(self):
        card = publisher.render_card(
            ITEM, records=1, bytes_=1024, first="r01", last="r01"
        )

        self.assertNotIn("## Record schema", card)

    def test_snapshot_keeps_legacy_baseline_and_filters_uncommitted_marker_batches(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "raw" / ITEM["slug"]
            destination_root = root / "hf"
            source.mkdir(parents=True)
            (source / ".round-marker-mode.json").write_text(
                '{"version":1,"legacy_baseline":1,"commit_point":"ROUND-rNN.complete.json"}\n'
            )
            write_valid_legacy(source / "batch-r01.jsonl")
            (source / "batch-r02.jsonl").write_text('{"id":"uncommitted"}\n')
            committed_batch = source / "batch-r03.jsonl"
            write_valid_completed_long_horizon(committed_batch, 3)
            committed_notes = source / "NOTES-r03.md"
            committed_notes.write_text("Novel coverage: 80%\ncommitted\n")
            (source / "ROUND-r03.complete.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "factory": ITEM["slug"],
                        "round": 3,
                        "records": 2,
                        "expected_records": 2,
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
            (source / "NOTES-r01.md").write_text("Novel coverage: 80%\nlegacy\n")
            (source / "NOTES-r02.md").write_text("uncommitted\n")

            self.assertEqual(
                [path.name for path in publisher.published_batches(source)],
                ["batch-r01.jsonl", "batch-r03.jsonl"],
            )
            stale_destination = (
                destination_root / publisher.HF_DATASETS_DIRNAME / ITEM["hub"] / "data" / "raw" / "batch-r02.jsonl"
            )
            stale_destination.parent.mkdir(parents=True)
            stale_destination.write_text('{"id":"stale"}\n')
            unknown_destination = stale_destination.parent / "uncommitted.jsonl"
            unknown_destination.write_text('{"id":"unvalidated"}\n')
            stale_note = destination_root / publisher.HF_DATASETS_DIRNAME / ITEM["hub"] / "data" / "metadata" / "NOTES-r02.md"
            stale_note.parent.mkdir(parents=True)
            stale_note.write_text("stale\n")
            unknown_metadata = stale_note.parent / "uncommitted.txt"
            unknown_metadata.write_text("must not publish\n")
            mirror = destination_root / publisher.HF_DATASETS_DIRNAME / ITEM["hub"]
            (mirror / "old.jsonl").write_text("must not publish\n")
            (mirror / "data" / "old.txt").write_text("must not publish\n")
            with mock.patch.object(publisher, "FACTORY_ROOT", root / "raw"), mock.patch.object(
                publisher, "HF_ROOT", destination_root
            ):
                publisher.snapshot_one(ITEM)
                raw = destination_root / publisher.HF_DATASETS_DIRNAME / ITEM["hub"] / "data" / "raw"
                self.assertTrue((raw / "batch-r01.jsonl").is_file())
                self.assertFalse((raw / "batch-r02.jsonl").exists())
                self.assertFalse((raw / "uncommitted.jsonl").exists())
                self.assertTrue((raw / "batch-r03.jsonl").is_file())
                meta = destination_root / publisher.HF_DATASETS_DIRNAME / ITEM["hub"] / "data" / "metadata"
                self.assertTrue((meta / "NOTES-r01.md").is_file())
                self.assertFalse((meta / "NOTES-r02.md").exists())
                self.assertTrue((meta / "NOTES-r03.md").is_file())
                self.assertFalse((meta / "uncommitted.txt").exists())
                self.assertFalse((mirror / "old.jsonl").exists())
                self.assertFalse((mirror / "data" / "old.txt").exists())

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
                card = (destination_root / publisher.HF_DATASETS_DIRNAME / "empty" / "README.md").read_text()
            self.assertIn("contains no published raw batch files", card)
            self.assertNotIn("batch-r01.jsonl` through", card)

    def test_snapshot_refuses_symlinked_payload_directories(self):
        for leaf in ("raw", "metadata"):
            with self.subTest(leaf=leaf), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                source = root / "raw" / ITEM["slug"]
                source.mkdir(parents=True)
                write_valid_legacy(source / "batch-r01.jsonl")
                outside = root / "outside"
                outside.mkdir()
                unsafe = root / "hf" / publisher.HF_DATASETS_DIRNAME / ITEM["hub"] / "data" / leaf
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
                write_valid_legacy(source / "batch-r01.jsonl")
                destination = root / "hf" / publisher.HF_DATASETS_DIRNAME / ITEM["hub"]
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
            write_valid_legacy(legacy)
            (source / "NOTES-r01.md").write_text(
                "Novel coverage: 80%\nlegacy notes\n"
            )

            self.assertEqual([path.name for path in publisher.published_batches(source)], ["episodes.jsonl"])
            with mock.patch.object(publisher, "FACTORY_ROOT", root / "raw"), mock.patch.object(
                publisher, "HF_ROOT", root / "hf"
            ):
                stats = publisher.snapshot_one(ITEM)

            raw = root / "hf" / publisher.HF_DATASETS_DIRNAME / ITEM["hub"] / "data" / "raw"
            meta = root / "hf" / publisher.HF_DATASETS_DIRNAME / ITEM["hub"] / "data" / "metadata"
            card = (root / "hf" / publisher.HF_DATASETS_DIRNAME / ITEM["hub"] / "README.md").read_text()
            self.assertEqual(stats["records"], 2)
            self.assertTrue((raw / legacy.name).is_file())
            self.assertTrue((meta / "NOTES-r01.md").is_file())
            self.assertIn("data/raw/episodes.jsonl", card)

            other = {**ITEM, "slug": "other-factory", "hub": "other"}
            other_source = root / "raw" / other["slug"]
            other_source.mkdir()
            write_valid_thalamic(other_source / "batch-r01.jsonl", "other")
            with mock.patch.object(publisher, "FACTORY_ROOT", root / "raw"), mock.patch.object(
                publisher, "HF_ROOT", root / "hf"
            ), mock.patch.object(publisher, "factories", return_value=[ITEM, other]):
                publisher.cmd_snapshot(other["hub"])
                local = publisher.local_snapshot_stats(ITEM)

            inventory = (root / "hf" / "SYNTHETIC-DATA-FACTORY-GROK46.md").read_text()
            self.assertEqual(local["records"], 2)
            self.assertIsNone(local["last"])
            # The inventory must point at the grouped mirror location an
            # operator will actually find on disk, not the pre-grouping path.
            group = publisher.HF_DATASETS_DIRNAME
            self.assertIn(f"| `{group}/{ITEM['hub']}/`", inventory)
            self.assertIn(f"| `{group}/{other['hub']}/`", inventory)
            self.assertNotIn(f"| `{ITEM['hub']}/`", inventory)
            self.assertIn(f"| `{publisher.HF_DATASETS_DIRNAME}/{other['hub']}/` |", inventory)
            self.assertIn(f"| `{other['slug']}` | 1 | 1 |", inventory)

    def test_snapshot_keeps_legacy_named_payload_before_marker_mode(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "raw" / ITEM["slug"]
            source.mkdir(parents=True)
            legacy = source / "episodes.jsonl"
            write_valid_legacy(legacy)
            notes = source / "NOTES-r01.md"
            notes.write_text("Novel coverage: 80%\nlegacy notes\n")

            self.assertEqual(
                [path.name for path in publisher.published_batches(source)],
                [legacy.name],
            )
            with mock.patch.object(
                publisher, "FACTORY_ROOT", root / "raw"
            ), mock.patch.object(publisher, "HF_ROOT", root / "hf"):
                stats = publisher.snapshot_one(ITEM)

            mirror = root / "hf" / publisher.HF_DATASETS_DIRNAME / ITEM["hub"]
            self.assertEqual(stats["records"], 2)
            self.assertTrue((mirror / "data" / "raw" / legacy.name).is_file())
            self.assertTrue((mirror / "data" / "metadata" / notes.name).is_file())
            self.assertIn(
                "data/raw/episodes.jsonl", (mirror / "README.md").read_text()
            )

    def test_pre_marker_payloads_must_pass_the_factory_contract(self):
        for payload, message in (
            ("{not-json\n", "JSON parse error"),
            (json.dumps({"id": "wrong-kind"}) + "\n", "requires only 'episode'"),
        ):
            with self.subTest(message=message), tempfile.TemporaryDirectory() as td:
                source = Path(td) / ITEM["slug"]
                source.mkdir()
                (source / "batch-r01.jsonl").write_text(payload)

                with self.assertRaisesRegex(SystemExit, message):
                    publisher.published_batches(source)

        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / ITEM["slug"]
            source.mkdir()
            batch = source / "batch-r01.jsonl"
            write_valid_legacy(batch)
            (source / "NOTES-r01.md").unlink()

            with self.assertRaisesRegex(SystemExit, "notes missing"):
                publisher.published_batches(source)

    def test_pre_marker_payload_ids_are_unique_across_factories(self):
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "outputs" / "raw" / "2099-01-01"
            source = run / ITEM["slug"]
            sibling = run / "other-factory"
            source.mkdir(parents=True)
            sibling.mkdir()
            records = [
                valid_legacy_episode("shared-id", success=True),
                valid_legacy_episode("unique-scenario-1", success=False),
            ]
            (source / "batch-r01.jsonl").write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )
            (source / "NOTES-r01.md").write_text("Novel coverage: 80%\n")
            write_valid_thalamic(sibling / "batch-r01.jsonl", "shared-id")

            with self.assertRaisesRegex(SystemExit, "duplicate record id 'shared-id'"):
                publisher.published_batches(source)

    def test_snapshot_publishes_canonical_notes_for_suffixed_legacy_batch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "raw" / ITEM["slug"]
            source.mkdir(parents=True)
            batch = source / "batch-r01a.jsonl"
            write_valid_legacy(batch)
            notes = source / "NOTES-r01.md"
            notes.write_text("Novel coverage: 80%\n")
            (source / ".round-marker-mode.json").write_text(
                '{"version":1,"legacy_baseline":1,"commit_point":"ROUND-rNN.complete.json"}\n'
            )

            with mock.patch.object(
                publisher, "FACTORY_ROOT", root / "raw"
            ), mock.patch.object(publisher, "HF_ROOT", root / "hf"):
                publisher.snapshot_one(ITEM)

            self.assertTrue(
                (root / "hf" / publisher.HF_DATASETS_DIRNAME / ITEM["hub"] / "data" / "raw" / batch.name).is_file()
            )
            self.assertTrue(
                (root / "hf" / publisher.HF_DATASETS_DIRNAME / ITEM["hub"] / "data" / "metadata" / notes.name).is_file()
            )

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
                        "version": 1,
                        "factory": "other-factory",
                        "round": 1,
                        "commit_point": marker.name,
                        "files": [],
                    },
                    "identity mismatch",
                ),
                (
                    {
                        "version": 1,
                        "factory": ITEM["slug"],
                        "round": 1,
                        "commit_point": "ROUND-r02.complete.json",
                        "files": [{"name": batch.name, "sha256": "0" * 64}],
                    },
                    "commit point mismatch",
                ),
                (
                    {
                        "version": 1,
                        "factory": ITEM["slug"],
                        "round": 1,
                        "commit_point": marker.name,
                        "files": [],
                    },
                    "no unique batch entry",
                ),
                (
                    {
                        "version": 1,
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
                        "version": 1,
                        "factory": source.name,
                        "round": 1,
                        "records": 2,
                        "expected_records": 2,
                        "commit_point": marker.name,
                        "files": [
                            {"name": "batch-r01.jsonl", "sha256": "0" * 64}
                        ],
                    }
                )
                + "\n"
            )
            stale = root / "hf" / publisher.HF_DATASETS_DIRNAME / ITEM["hub"] / "data" / "raw" / "batch-r01.jsonl"
            stale.parent.mkdir(parents=True)
            stale.write_text('{"id":"preserve"}\n')

            with mock.patch.object(publisher, "FACTORY_ROOT", root / "raw"), mock.patch.object(
                publisher, "HF_ROOT", root / "hf"
            ):
                with self.assertRaisesRegex(SystemExit, "unsafe committed artifact"):
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
                        "version": 1,
                        "factory": source.name,
                        "round": 1,
                        "records": 2,
                        "expected_records": 2,
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
            stale = root / "hf" / publisher.HF_DATASETS_DIRNAME / ITEM["hub"] / "data" / "metadata" / notes.name
            stale.parent.mkdir(parents=True)
            stale.write_text("preserve\n")

            with mock.patch.object(publisher, "FACTORY_ROOT", root / "raw"), mock.patch.object(
                publisher, "HF_ROOT", root / "hf"
            ):
                with self.assertRaisesRegex(SystemExit, "unsafe committed artifact"):
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
            write_valid_completed_long_horizon(batch, 1)
            notes.write_text("Novel coverage: 80%\n")
            evidence.write_text('{"result":"passed"}\n')
            marker = source / "ROUND-r01.complete.json"
            marker.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "factory": source.name,
                        "round": 1,
                        "records": 2,
                        "expected_records": 2,
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
            write_valid_legacy(source / "batch-r01.jsonl")
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
            write_valid_legacy(source / "episodes.jsonl")
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

    def test_marker_mode_cannot_hide_a_legacy_batch_r01(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / ITEM["slug"]
            source.mkdir()
            write_valid_legacy(source / "batch-r01.jsonl")
            (source / ".round-marker-mode.json").write_text(
                '{"version":1,"legacy_baseline":0,"commit_point":"ROUND-rNN.complete.json"}\n'
            )

            with self.assertRaisesRegex(SystemExit, "excludes legacy r01"):
                publisher.published_batches(source)

    def test_marker_mode_rejects_a_malformed_named_legacy_frontier(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / ITEM["slug"]
            source.mkdir()
            (source / "batch-r26.jsonl").write_text("{not-json\n")
            (source / ".round-marker-mode.json").write_text(
                '{"version":1,"legacy_baseline":26,"commit_point":"ROUND-rNN.complete.json"}\n'
            )

            with self.assertRaisesRegex(SystemExit, "exceeds discovered legacy frontier"):
                publisher.published_batches(source)

    def test_marker_mode_rejects_malformed_payload_below_valid_legacy_frontier(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / ITEM["slug"]
            source.mkdir()
            (source / "batch-r25.jsonl").write_text("{not-json\n")
            write_valid_legacy(source / "batch-r26.jsonl")
            (source / ".round-marker-mode.json").write_text(
                '{"version":1,"legacy_baseline":26,"commit_point":"ROUND-rNN.complete.json"}\n'
            )

            with self.assertRaisesRegex(
                SystemExit, "invalid legacy payload covered by marker baseline"
            ):
                publisher.published_batches(source)

    def test_snapshot_rechecks_manifest_digest_after_visibility_selection(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "raw" / ITEM["slug"]
            source.mkdir(parents=True)
            batch = source / "batch-r01.jsonl"
            notes = source / "NOTES-r01.md"
            write_valid_completed_long_horizon(batch, 1)
            notes.write_text("Novel coverage: 80%\ncommitted\n")
            (source / ".round-marker-mode.json").write_text(
                '{"version":1,"legacy_baseline":0,"commit_point":"ROUND-rNN.complete.json"}\n'
            )
            (source / "ROUND-r01.complete.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "factory": ITEM["slug"],
                        "round": 1,
                        "records": 2,
                        "expected_records": 2,
                        "commit_point": "ROUND-r01.complete.json",
                        "files": [
                            {"name": batch.name, "sha256": hashlib.sha256(batch.read_bytes()).hexdigest()},
                            {"name": notes.name, "sha256": hashlib.sha256(notes.read_bytes()).hexdigest()},
                        ],
                    }
                )
                + "\n"
            )
            real_published_notes = publisher.published_notes

            def tamper_after_selection(*args, **kwargs):
                selected = real_published_notes(*args, **kwargs)
                batch.write_text('{"id":"changed-after-validation"}\n')
                return selected

            with mock.patch.object(publisher, "FACTORY_ROOT", root / "raw"), mock.patch.object(
                publisher, "HF_ROOT", root / "hf"
            ), mock.patch.object(
                publisher, "published_notes", side_effect=tamper_after_selection
            ):
                with self.assertRaisesRegex(SystemExit, "changed after manifest validation"):
                    publisher.snapshot_one(ITEM)

            self.assertFalse((root / "hf" / publisher.HF_DATASETS_DIRNAME / ITEM["hub"] / "data" / "raw" / batch.name).exists())

    def test_snapshot_rechecks_legacy_digest_after_visibility_selection(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "raw" / ITEM["slug"]
            source.mkdir(parents=True)
            batch = source / "batch-r01.jsonl"
            write_valid_legacy(batch)
            (source / "NOTES-r01.md").write_text("Novel coverage: 80%\n")
            (source / ".round-marker-mode.json").write_text(
                '{"version":1,"legacy_baseline":1,"commit_point":"ROUND-rNN.complete.json"}\n'
            )
            real_published_notes = publisher.published_notes

            def tamper_after_selection(*args, **kwargs):
                selected = real_published_notes(*args, **kwargs)
                batch.write_text('{"id":"changed-after-validation"}\n')
                return selected

            with mock.patch.object(
                publisher, "FACTORY_ROOT", root / "raw"
            ), mock.patch.object(
                publisher, "HF_ROOT", root / "hf"
            ), mock.patch.object(
                publisher, "published_notes", side_effect=tamper_after_selection
            ):
                with self.assertRaisesRegex(
                    SystemExit, "changed after manifest validation"
                ):
                    publisher.snapshot_one(ITEM)

            self.assertFalse(
                (root / "hf" / publisher.HF_DATASETS_DIRNAME / ITEM["hub"] / "data" / "raw" / batch.name).exists()
            )

    def test_snapshot_rechecks_pre_marker_digest_after_validation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "raw" / ITEM["slug"]
            source.mkdir(parents=True)
            batch = source / "batch-r01.jsonl"
            write_valid_legacy(batch)
            real_published_notes = publisher.published_notes

            def tamper_after_selection(*args, **kwargs):
                selected = real_published_notes(*args, **kwargs)
                batch.write_text('{"id":"changed-after-validation"}\n')
                return selected

            with mock.patch.object(
                publisher, "FACTORY_ROOT", root / "raw"
            ), mock.patch.object(
                publisher, "HF_ROOT", root / "hf"
            ), mock.patch.object(
                publisher, "published_notes", side_effect=tamper_after_selection
            ):
                with self.assertRaisesRegex(
                    SystemExit, "changed after manifest validation"
                ):
                    publisher.snapshot_one(ITEM)

            self.assertFalse(
                (root / "hf" / publisher.HF_DATASETS_DIRNAME / ITEM["hub"] / "data" / "raw" / batch.name).exists()
            )

    def test_snapshot_rechecks_pre_marker_note_digest_after_validation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "raw" / ITEM["slug"]
            source.mkdir(parents=True)
            batch = source / "batch-r01.jsonl"
            write_valid_legacy(batch)
            notes = source / "NOTES-r01.md"
            real_published_notes = publisher.published_notes

            def tamper_after_selection(*args, **kwargs):
                selected = real_published_notes(*args, **kwargs)
                notes.write_text("Novel coverage: changed after validation\n")
                return selected

            with mock.patch.object(
                publisher, "FACTORY_ROOT", root / "raw"
            ), mock.patch.object(
                publisher, "HF_ROOT", root / "hf"
            ), mock.patch.object(
                publisher, "published_notes", side_effect=tamper_after_selection
            ):
                with self.assertRaisesRegex(
                    SystemExit, "changed after manifest validation"
                ):
                    publisher.snapshot_one(ITEM)

            self.assertFalse(
                (root / "hf" / publisher.HF_DATASETS_DIRNAME / ITEM["hub"] / "data" / "metadata" / notes.name).exists()
            )

    def test_invalid_utf8_completion_marker_has_a_bounded_error(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / ITEM["slug"]
            source.mkdir()
            (source / "ROUND-r01.complete.json").write_bytes(b"\xff\n")

            with self.assertRaisesRegex(
                SystemExit, r"cannot read .*ROUND-r01\.complete\.json"
            ):
                publisher.completed_manifests(source)

    def test_marker_mode_validates_completion_manifests_once(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / ITEM["slug"]
            source.mkdir()
            (source / ".round-marker-mode.json").write_text(
                '{"version":1,"legacy_baseline":0,"commit_point":"ROUND-rNN.complete.json"}\n'
            )

            with mock.patch.object(
                publisher, "transaction_completed_manifests", return_value={}
            ) as validate:
                publisher.marker_mode_state(source)

            validate.assert_called_once_with(source)

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
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "raw" / ITEM["slug"]
            source.mkdir(parents=True)
            write_valid_legacy(source / "batch-r01.jsonl")
            with mock.patch.object(
                publisher, "FACTORY_ROOT", root / "raw"
            ), mock.patch.object(publisher, "HF_ROOT", root / "hf"), mock.patch.object(
                publisher, "factories", return_value=[ITEM]
            ), mock.patch.object(publisher, "run") as run:
                publisher.snapshot_one(ITEM)
                publisher.cmd_upload()

        command = run.call_args.args[0]
        self.assertIn("--delete", command)
        self.assertEqual(
            [command[index + 1] for index, value in enumerate(command) if value == "--delete"],
            ["data/raw/*", "data/metadata/NOTES-r*.md"],
        )

    def test_upload_refuses_payload_changed_after_snapshot(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "raw" / ITEM["slug"]
            source.mkdir(parents=True)
            batch = source / "batch-r01.jsonl"
            write_valid_legacy(batch)
            with mock.patch.object(
                publisher, "FACTORY_ROOT", root / "raw"
            ), mock.patch.object(publisher, "HF_ROOT", root / "hf"), mock.patch.object(
                publisher, "factories", return_value=[ITEM]
            ), mock.patch.object(publisher, "run") as run:
                publisher.snapshot_one(ITEM)
                mirror_batch = root / "hf" / publisher.HF_DATASETS_DIRNAME / ITEM["hub"] / "data" / "raw" / batch.name
                mirror_batch.write_text('{"id":"unrelated"}\n')

                with self.assertRaisesRegex(SystemExit, "upload snapshot digest mismatch"):
                    publisher.cmd_upload()

            run.assert_not_called()

    def test_snapshot_refuses_a_symlinked_datasets_root(self):
        # The per-model mirror root gets the same symlink rejection as the Hub
        # root; without this the grouping directory would be an escape hatch.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            hub_root = root / "hf"
            outside = root / "outside"
            hub_root.mkdir()
            outside.mkdir()
            (hub_root / publisher.HF_DATASETS_DIRNAME).symlink_to(
                outside, target_is_directory=True
            )
            dest = hub_root / publisher.HF_DATASETS_DIRNAME / ITEM["hub"]

            with mock.patch.object(publisher, "HF_ROOT", hub_root):
                with self.assertRaisesRegex(SystemExit, "unsafe snapshot directory"):
                    publisher.snapshot_directories(dest)

    def test_snapshot_refuses_a_destination_outside_the_datasets_root(self):
        # A mirror written directly under the Hub root (the pre-grouping
        # layout) must be rejected rather than silently accepted.
        with tempfile.TemporaryDirectory() as td:
            hub_root = Path(td) / "hf"
            hub_root.mkdir(parents=True)

            with mock.patch.object(publisher, "HF_ROOT", hub_root):
                with self.assertRaisesRegex(
                    SystemExit, "snapshot destination escaped Hub root"
                ):
                    publisher.snapshot_directories(hub_root / ITEM["hub"])

    def test_upload_refuses_a_missing_datasets_root(self):
        # HF_ROOT can exist while the per-model mirror root does not; the
        # upload guard must reject that instead of proceeding.
        with tempfile.TemporaryDirectory() as td:
            hub_root = Path(td) / "hf"
            hub_root.mkdir(parents=True)

            with mock.patch.object(publisher, "HF_ROOT", hub_root):
                with self.assertRaisesRegex(SystemExit, "unsafe upload root"):
                    publisher.safe_upload_directory(ITEM)

    def test_upload_refuses_a_symlinked_hub_mirror(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            hub_root = root / "hf"
            outside = root / "outside"
            datasets_root = hub_root / publisher.HF_DATASETS_DIRNAME
            datasets_root.mkdir(parents=True)
            outside.mkdir()
            (datasets_root / ITEM["hub"]).symlink_to(outside, target_is_directory=True)

            with mock.patch.object(publisher, "HF_ROOT", hub_root), mock.patch.object(
                publisher, "factories", return_value=[ITEM]
            ), mock.patch.object(publisher, "run") as run:
                with self.assertRaisesRegex(SystemExit, "unsafe upload directory"):
                    publisher.cmd_upload()

            run.assert_not_called()

    def test_upload_refuses_unmanaged_files_outside_payload_directories(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "hf"
            mirror = root / publisher.HF_DATASETS_DIRNAME / ITEM["hub"]
            mirror.mkdir(parents=True)
            (mirror / "old.jsonl").write_text("unmanaged\n")

            with mock.patch.object(publisher, "HF_ROOT", root), mock.patch.object(
                publisher, "factories", return_value=[ITEM]
            ), mock.patch.object(publisher, "run") as run:
                with self.assertRaisesRegex(SystemExit, "unmanaged upload tree entry"):
                    publisher.cmd_upload()

            run.assert_not_called()

    def test_status_counts_only_marker_visible_factory_batches(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "raw" / ITEM["slug"]
            source.mkdir(parents=True)
            (source / ".round-marker-mode.json").write_text(
                '{"version":1,"legacy_baseline":0,"commit_point":"ROUND-rNN.complete.json"}\n'
            )
            write_valid_completed_long_horizon(source / "batch-r01.jsonl", 1)
            (source / "ROUND-r01.publishing.json").write_text("{}\n")

            with mock.patch.object(
                publisher, "FACTORY_ROOT", root / "raw"
            ), mock.patch.object(
                publisher, "HF_ROOT", root / "hf"
            ), mock.patch.object(
                publisher, "factories", return_value=[ITEM]
            ), mock.patch("builtins.print") as print_:
                publisher.cmd_status()

            row = print_.call_args_list[-1].args[0]
            self.assertRegex(row, r"\s+0\s+0$")

    def test_targeted_snapshot_preserves_full_inventory(self):
        other = {**ITEM, "slug": "other-factory", "hub": "other"}
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for item, record_id in ((ITEM, "selected"), (other, "other")):
                source = root / "raw" / item["slug"]
                source.mkdir(parents=True)
                batch = source / "batch-r01.jsonl"
                if item == ITEM:
                    write_valid_legacy(batch)
                else:
                    write_valid_thalamic(batch, record_id)
            with mock.patch.object(publisher, "FACTORY_ROOT", root / "raw"), mock.patch.object(
                publisher, "HF_ROOT", root / "hf"
            ), mock.patch.object(publisher, "factories", return_value=[ITEM, other]):
                publisher.cmd_snapshot()
                publisher.cmd_snapshot(ITEM["hub"])

            inventory = (root / "hf" / "SYNTHETIC-DATA-FACTORY-GROK46.md").read_text()
            self.assertIn(f"`{publisher.HF_DATASETS_DIRNAME}/{ITEM['hub']}/`", inventory)
            self.assertIn(f"`{publisher.HF_DATASETS_DIRNAME}/{other['hub']}/`", inventory)
            self.assertIn(f"| `{other['slug']}` | 1 | 1 |", inventory)

    def test_all_only_scopes_every_publish_stage(self):
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
        create.assert_called_once_with(ITEM["hub"])
        collect.assert_called_once_with(ITEM["hub"])

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

    def test_local_commands_skip_hub_authentication(self):
        for command, handler_name in (("snapshot", "cmd_snapshot"), ("status", "cmd_status")):
            with self.subTest(command=command), mock.patch.object(
                publisher.subprocess, "run"
            ) as whoami, mock.patch.object(
                publisher, handler_name
            ) as handler, mock.patch.object(
                sys, "argv", ["publish_grok46_hub.py", command]
            ):
                self.assertEqual(publisher.main(), 0)

            whoami.assert_not_called()
            if command == "snapshot":
                handler.assert_called_once_with(None)
            else:
                handler.assert_called_once_with()

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
