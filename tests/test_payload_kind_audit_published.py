#!/usr/bin/env python3
"""Pin the published #74 payload-kind finding to its committed evidence.

Split out of test_payload_kind_audit.py: these assertions need no Hub access
and no gitignored raw tree, so they live apart from the corpus-fidelity check
in test_payload_kind_audit_fidelity.py and from the general classification
behavior in test_payload_kind_audit.py.
"""

import json
import sys
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from payload_kind_audit_fixtures import (  # noqa: E402
    AUDIT_DOC,
    AUDIT_JSON,
    DERIVED_KEYS,
    ISSUE_74_THALAMIC_IDS,
    REPO,
)

PIPELINES = REPO / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import payload_kind_audit  # noqa: E402


class PublishedAgenticCodingPayloadKindAudit(unittest.TestCase):
    """Pin the #74 finding from the committed evidence alone.

    These assertions need no Hub access and no gitignored raw tree: they hold
    the committed audit to its own arithmetic, and hold the write-up to the
    committed audit. If either drifts, the numbers quoted in the PR and in the
    card text stop agreeing with each other here first.
    """

    @classmethod
    def setUpClass(cls):
        cls.audit = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
        cls.doc = AUDIT_DOC.read_text(encoding="utf-8")

    def test_the_committed_audit_balances(self):
        summary = self.audit["summary"]
        self.assertEqual(summary["files"], len(self.audit["files"]))
        self.assertEqual(summary["records"], len(self.audit["records"]))
        self.assertEqual(sum(summary["kinds"].values()), summary["records"])
        self.assertEqual(sum(entry["records"] for entry in self.audit["files"]), summary["records"])
        steps = summary["coding_steps"]
        self.assertEqual(steps["native"] + steps["wrapped"], steps["total"])
        self.assertEqual(
            summary["coding_episodes_including_wrapped"],
            summary["coding_episodes_reachable_at_top_level"]
            + summary["thalamic_records_wrapping_a_coding_episode"],
        )

    def test_generated_audit_and_supplementary_evidence_are_distinct(self):
        provenance = self.audit["document_provenance"]
        generated = provenance["generated_audit"]
        supplementary = provenance["supplementary_evidence"]

        self.assertNotIn("generated_by", self.audit)
        self.assertEqual(generated["generated_by"], "pipelines/payload_kind_audit.py")
        self.assertEqual(tuple(generated["fields"]), DERIVED_KEYS)
        self.assertIn("not emitted by the audit pipeline", supplementary["description"])

        generated_fields = set(generated["fields"])
        supplementary_fields = set(supplementary["fields"])
        self.assertTrue(generated_fields.isdisjoint(supplementary_fields))
        self.assertEqual(
            generated_fields | supplementary_fields,
            set(self.audit) - {"document_provenance"},
        )

    def test_the_payload_kind_split_is_three_episodes_and_sixteen_gate_records(self):
        summary = self.audit["summary"]
        self.assertEqual(summary["records"], 19)
        self.assertEqual(summary["kinds"], {"episode": 3, "thalamic": 16})
        # The whole point of #74: a top-level coding-episode loader reaches 3.
        self.assertEqual(summary["coding_episodes_reachable_at_top_level"], 3)
        # And the sibling scan's point: every gate record does wrap one.
        self.assertEqual(summary["thalamic_records_wrapping_a_coding_episode"], 16)
        self.assertEqual(summary["coding_episodes_including_wrapped"], 19)

    def test_all_three_episodes_live_in_the_legacy_filename_and_carry_no_id(self):
        episodes = [row for row in self.audit["records"] if row["kind"] == "episode"]
        self.assertEqual(len(episodes), 3)
        self.assertEqual({row["source_file"] for row in episodes}, {"episodes.jsonl"})
        self.assertEqual([row["source_line"] for row in episodes], [1, 2, 3])
        self.assertEqual([row["id"] for row in episodes], [None, None, None])
        # A batch-only glob would drop the one file that holds every coding
        # episode: no batch shard contributes a single episode record.
        batch_files = [entry for entry in self.audit["files"] if entry["path"].startswith("batch-")]
        self.assertEqual(len(batch_files), 8)
        self.assertEqual(sum(entry["kinds"].get("episode", 0) for entry in batch_files), 0)

    def test_the_gate_record_ids_are_the_sixteen_the_issue_lists(self):
        gate_ids = tuple(row["id"] for row in self.audit["records"] if row["kind"] == "thalamic")
        self.assertEqual(gate_ids, ISSUE_74_THALAMIC_IDS)
        self.assertTrue(
            all(
                row["wraps_coding_episode"]
                for row in self.audit["records"]
                if row["kind"] == "thalamic"
            )
        )

    def test_no_published_step_carries_decision_basis(self):
        fields = self.audit["summary"]["coding_steps_by_reasoning_field"]
        total = self.audit["summary"]["coding_steps"]["total"]
        self.assertEqual(total, 361)
        self.assertEqual(fields["decision_basis"], 0)
        self.assertEqual(fields["thought"], total)
        self.assertEqual(fields["reflection"], total)
        # #74 counts only the 3 top-level episodes' 77 steps.
        self.assertEqual(self.audit["summary"]["coding_steps"]["native"], 77)

    def test_every_record_is_stamped_by_this_factory(self):
        self.assertEqual(
            self.audit["summary"]["meta_factory_stamps"],
            {"agentic-coding-trajectory-factory": self.audit["summary"]["records"]},
        )

    def test_the_viewer_projection_is_recorded_as_healthy_and_complete(self):
        viewer = self.audit["hub"]["viewer"]
        self.assertTrue(viewer["healthy"])
        self.assertTrue(viewer["lossless_against_raw"])
        self.assertEqual(viewer["rows"], self.audit["summary"]["records"])
        self.assertEqual(
            viewer["rows_by_source_file"],
            {entry["path"]: entry["records"] for entry in self.audit["files"]},
        )
        # The fix must stay card-side: no default config over data/raw/*.jsonl.
        self.assertIn("must not be replaced by", self.audit["card_disclosure"]["markdown"])

    def test_no_card_schema_declaration_was_added_for_this_dataset(self):
        # agentic-coding-trajectories is a Fable-5 dataset. The card-schema
        # mechanism belongs to the Grok 4.6 publisher, which does not manage it;
        # a declaration file here would be orphaned.
        self.assertFalse(
            (REPO / "config" / "card-schemas" / "agentic-coding-trajectories.json").exists()
        )

    def test_the_write_up_carries_the_generated_record_table_verbatim(self):
        self.assertIn(payload_kind_audit.render_markdown(self.audit), self.doc)

    def test_the_write_up_carries_the_card_disclosure_verbatim(self):
        opening = "```markdown\n"
        start = self.doc.index(opening) + len(opening)
        end = self.doc.index("\n```", start) + 1
        self.assertEqual(self.doc[start:end], self.audit["card_disclosure"]["markdown"])

    def test_the_card_corrections_name_the_stale_license_claim(self):
        corrections = self.audit["card_corrections"]
        self.assertTrue(corrections)
        for row in corrections:
            self.assertEqual({"field", "current", "replacement", "why"}, set(row))
            for value in row.values():
                self.assertIsInstance(value, str)
                self.assertTrue(value.strip())
        fields = " ".join(row["field"] for row in corrections)
        self.assertIn("release-status.json", fields)
        self.assertIn(
            "apache-2.0",
            " ".join(row["replacement"] for row in corrections).lower(),
        )

    def test_the_write_up_names_the_modules_that_substantiate_it(self):
        """The verification guide must send a reader to modules that exist and
        that actually hold the two checks it describes."""
        for module, marker in (
            ("tests/test_payload_kind_audit_published.py", "test_the_committed_audit_balances"),
            (
                "tests/test_payload_kind_audit_fidelity.py",
                "test_the_published_audit_is_a_fresh_scan_of_the_raw_corpus",
            ),
        ):
            with self.subTest(module=module):
                self.assertIn(module, self.doc)
                path = REPO / module
                self.assertTrue(path.exists(), f"{module} named by the write-up is missing")
                self.assertIn(marker, path.read_text(encoding="utf-8"))

    def test_the_write_up_says_the_hub_write_is_not_done_here(self):
        self.assertIn("Nothing was uploaded to the Hugging Face Hub", self.doc)


if __name__ == "__main__":
    unittest.main()
