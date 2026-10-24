"""Every record kind is scanned for denylist identity fields (#508)."""

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))
import eval_exclusion_subject as subject  # noqa: E402
from eval_exclusion_policy import SourceIdentity  # noqa: E402


class SourceIdentityTests(unittest.TestCase):
    def test_code_repair_and_real_public_engineering_keep_their_rules(self):
        repair = {"family": "python-function-repair",
                  "scenario": {"source": {"program_id": "tap-0",
                                          "upstream": {"repository": "TheAlgorithms/Python"}}}}
        real = {"source_kind": "real_public_engineering",
                "environment": {"source_repo": "clap-rs/clap", "task_id": "t-1"}}
        self.assertEqual(subject.source_identity(repair)[0], subject.RULE_CODE_REPAIR)
        self.assertEqual(subject.source_identity(real)[0], subject.RULE_REAL_PUBLIC_ENGINEERING)

    def test_records_without_identity_fields_are_ungoverned(self):
        for record in ({"goal": "g", "steps": []}, {"source_kind": "synthetic"}, ["x"], None):
            with self.subTest(record=record):
                self.assertIsNone(subject.source_identity(record))
                self.assertEqual(subject.source_identities(record), [])

    def test_payload_scan_covers_nested_program_and_task_ids_on_other_kinds(self):
        episode = {"goal": "g", "steps": [], "meta": {"program_id": "tap-held"}}
        preference = {"chosen": {"task_id": "board-1"}, "rejected": {"x": 1}}
        episode_rule, episode_identity = subject.source_identity(episode)
        preference_rule, preference_identity = subject.source_identity(preference)
        self.assertEqual(episode_rule, subject.RULE_PAYLOAD)
        self.assertEqual(episode_identity, SourceIdentity(repo=None, program_id="tap-held"))
        self.assertEqual(preference_rule, subject.RULE_PAYLOAD)
        self.assertEqual(preference_identity, SourceIdentity(repo=None, task_id="board-1"))
        self.assertFalse(subject.requires_repo(subject.RULE_PAYLOAD))
        self.assertTrue(subject.requires_repo(subject.RULE_CODE_REPAIR))

    def test_payload_scan_covers_nested_repository_keys(self):
        episode = {"goal": "g", "steps": [], "meta": {"repository": "clap-rs/clap"}}
        rule, identity = subject.source_identity(episode)
        self.assertEqual(rule, subject.RULE_PAYLOAD)
        self.assertEqual(identity, SourceIdentity("clap-rs/clap"))

    def test_payload_scan_evaluates_every_repository(self):
        record = {
            "chosen": {"repository": "someone/else"},
            "rejected": {"repository": "clap-rs/clap"},
        }
        repos = [identity.repo for _rule, identity in subject.source_identities(record)]
        self.assertCountEqual(repos, ["someone/else", "clap-rs/clap"])

    def test_instance_id_maps_to_owner_slash_name(self):
        self.assertEqual(subject.repo_from_instance_id("clap-rs__clap-5873"), "clap-rs/clap")
        self.assertEqual(subject.repo_from_instance_id("burntsushi__ripgrep-12"),
                         "burntsushi/ripgrep")
        self.assertIsNone(subject.repo_from_instance_id("not-an-instance"))
        record = {"instance_id": "clap-rs__clap-5873"}
        rule, identity = subject.source_identity(record)
        self.assertEqual(rule, subject.RULE_PAYLOAD)
        self.assertEqual(identity, SourceIdentity("clap-rs/clap"))
