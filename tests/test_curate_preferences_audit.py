#!/usr/bin/env python3
"""The published same-state audit: reconciliation, rendering, and the CLI."""

import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path

from preference_test_support import (  # noqa: E402
    GENERATED_TABLE_END,
    GENERATED_TABLE_START,
    PROPOSAL_ONLY_IMPURE,
    PUBLISHED_AUDIT,
    PUBLISHED_AUDIT_DOC,
    PURITY_FIXTURES,
    audit_decision_map,
    leftover_mill_episode,
    pair,
    run_cli,
    write_jsonl,
)
import curate_preferences  # noqa: E402


class SameStateAuditReconciliation(unittest.TestCase):
    """Bind the Hub 17/42 and factory 19/42 counts to one decomposition."""

    @classmethod
    def setUpClass(cls):
        cls.curation_run = curate_preferences.curate_source(PURITY_FIXTURES)
        cls.audit = curate_preferences.build_audit(cls.curation_run)

    def test_scan_splits_the_nineteen_into_state_and_proposal_divergence(self):
        summary = self.curation_run.summary
        self.assertEqual(summary["preference_records"], 42)
        self.assertEqual(summary["impure_pairs"], 19)
        # The Hub-side same_state audit measures exactly this subset.
        self.assertEqual(summary["state_divergent_pairs"], 17)
        self.assertEqual(summary["same_state_pairs"], 25)
        self.assertEqual(summary["proposed_action_divergent_pairs"], 14)
        self.assertEqual(summary["same_proposed_action_pairs"], 28)
        self.assertEqual(summary["state_only_divergent_pairs"], 5)
        self.assertEqual(summary["proposed_action_only_divergent_pairs"], 2)
        self.assertEqual(summary["both_context_fields_divergent_pairs"], 12)
        self.assertEqual(summary["context_undetermined_pairs"], 0)
        # 17 = 5 + 12 and 19 = 17 + 2, with no pair counted twice.
        self.assertEqual(
            summary["state_only_divergent_pairs"] + summary["both_context_fields_divergent_pairs"],
            summary["state_divergent_pairs"],
        )
        self.assertEqual(
            summary["state_divergent_pairs"] + summary["proposed_action_only_divergent_pairs"],
            summary["impure_pairs"],
        )
        self.assertEqual(
            summary["same_state_pairs"] + summary["state_divergent_pairs"],
            summary["preference_records"],
        )

    def test_the_two_proposal_only_pairs_are_invisible_to_a_state_audit(self):
        by_location = {
            (pair_entry["source_path"], pair_entry["source_line"]): pair_entry
            for pair_entry in self.audit["impure_pairs"]
        }
        self.assertEqual(len(by_location), 19)
        for location in PROPOSAL_ONLY_IMPURE:
            entry = by_location[location]
            self.assertIs(entry["same_state"], True, location)
            self.assertIs(entry["same_proposed_action"], False, location)
            self.assertEqual(entry["divergent_context_fields"], ["proposed_action"], location)
        state_divergent = [entry for entry in by_location.values() if entry["same_state"] is False]
        self.assertEqual(len(state_divergent), 17)

    def test_every_audited_pair_names_a_reason_and_a_diverging_field(self):
        for entry in self.audit["impure_pairs"]:
            location = (entry["source_path"], entry["source_line"])
            self.assertTrue(entry["reason_codes"], location)
            self.assertTrue(entry["context_diff_paths"], location)
            self.assertTrue(entry["divergent_context_fields"], location)
            self.assertIn(
                entry["action"],
                (curate_preferences.ACTION_REPAIRED, curate_preferences.ACTION_EXCLUDED),
                location,
            )
            expected_fields = [
                field
                for field, same in (
                    ("state", entry["same_state"]),
                    ("proposed_action", entry["same_proposed_action"]),
                )
                if same is False
            ]
            self.assertEqual(entry["divergent_context_fields"], expected_fields, location)

    def test_retained_pairs_are_absent_from_the_audit(self):
        audited = {
            (entry["source_path"], entry["source_line"]) for entry in self.audit["impure_pairs"]
        }
        retained = {
            (entry["source_path"], entry["source_line"])
            for entry in self.curation_run.manifest
            if entry["action"] == curate_preferences.ACTION_RETAINED
        }
        self.assertEqual(len(retained), 23)
        self.assertFalse(audited & retained)

    def test_markdown_render_carries_the_reconciliation_and_every_pair(self):
        markdown = curate_preferences.render_audit_markdown(self.audit)
        self.assertIn("| `same_state = false` (state diverges) | 17 |", markdown)
        self.assertIn("| `same_proposed_action = false` (proposal diverges) | 14 |", markdown)
        self.assertIn("| Impure pairs (either field diverges) | 19 |", markdown)
        self.assertIn("| - proposed action only | 2 |", markdown)
        self.assertIn("| Curated same-context purity | 100.0% |", markdown)
        rows = [line for line in markdown.splitlines() if line.startswith("| `ffpc")]
        anonymous = [
            line for line in markdown.splitlines() if line.startswith("| _(no record id)_")
        ]
        self.assertEqual(len(rows) + len(anonymous), 19)
        self.assertEqual(len(anonymous), 6)


class PublishedSameStateAudit(unittest.TestCase):
    """The committed public audit must stay bound to reproducible decisions."""

    @classmethod
    def setUpClass(cls):
        cls.published = json.loads(PUBLISHED_AUDIT.read_text(encoding="utf-8"))
        cls.doc = PUBLISHED_AUDIT_DOC.read_text(encoding="utf-8")
        cls.fixture_audit = curate_preferences.build_audit(
            curate_preferences.curate_source(PURITY_FIXTURES)
        )

    def test_published_summary_matches_the_fixture_corpus(self):
        self.assertEqual(self.published["schema_version"], curate_preferences.AUDIT_SCHEMA_VERSION)
        self.assertEqual(self.published["audit"], curate_preferences.AUDIT_NAME)
        self.assertEqual(
            self.published["transform"],
            {
                "name": curate_preferences.TRANSFORM_NAME,
                "version": curate_preferences.TRANSFORM_VERSION,
            },
        )
        self.assertEqual(self.published["summary"], self.fixture_audit["summary"])

    def test_published_decisions_match_the_fixture_corpus_line_for_line(self):
        self.assertEqual(
            audit_decision_map(self.published),
            audit_decision_map(self.fixture_audit),
        )

    def test_published_audit_covers_every_source_file_digest(self):
        self.assertEqual(
            [entry["source_path"] for entry in self.published["source_files"]],
            [path.name for path in sorted(PURITY_FIXTURES.glob("*.jsonl"))],
        )
        self.assertEqual(len(self.published["source_files"]), 10)
        for entry in self.published["source_files"]:
            self.assertRegex(entry["source_file_sha256"], r"^[0-9a-f]{64}$")

    def test_published_pairs_name_the_raw_record_ids_and_source_lines(self):
        ids = [entry["record_id"] for entry in self.published["impure_pairs"]]
        self.assertEqual(len(ids), 19)
        self.assertIn("ffpc-r2-001", ids)
        self.assertIn("ffpc-r3-004", ids)
        # The round-1 file carries a thinner schema with no top-level id.
        self.assertEqual(ids.count(None), 6)
        for entry in self.published["impure_pairs"]:
            self.assertRegex(entry["source_sha256"], r"^[0-9a-f]{64}$")
            self.assertIsInstance(entry["source_line"], int)

    def test_published_markdown_block_is_generated_from_the_published_audit(self):
        start = self.doc.index(GENERATED_TABLE_START) + len(GENERATED_TABLE_START)
        end = self.doc.index(GENERATED_TABLE_END)
        block = self.doc[start:end].strip("\n")
        self.assertEqual(block, curate_preferences.render_audit_markdown(self.published))

    def test_published_doc_states_the_card_limitation_claims(self):
        self.assertIn("## Limitations", self.doc)
        self.assertIn("**17 have `same_state = false`**", self.doc)
        self.assertIn("**19 of 42\npairs are impure**", self.doc)
        self.assertIn("**Do not train on `data/raw/`.**", self.doc)
        self.assertIn("ffpc-r5-002", self.doc)
        self.assertIn("ffpc-r5-003", self.doc)


class AuditAndReconcileCli(unittest.TestCase):
    def test_audit_separates_equal_context_exclusions_from_impurity(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "preferences.jsonl"
            malformed = pair("equal-context-nonfinite")
            malformed["reward_delta"] = float("nan")
            write_jsonl(source, [malformed])

            run = curate_preferences.curate_source(source)
            self.assertEqual(run.summary["preference_records"], 1)
            self.assertEqual(run.summary["excluded_pairs"], 1)
            self.assertEqual(run.summary["impure_pairs"], 0)
            self.assertIs(run.manifest[0]["same_state"], True)
            self.assertIs(run.manifest[0]["same_proposed_action"], True)

            status, stdout, stderr = run_cli("audit", str(source), "--json")

        self.assertEqual(status, 0, stderr)
        audit = json.loads(stdout)
        self.assertEqual(audit["summary"]["preference_pairs"], 1)
        self.assertEqual(audit["summary"]["impure_pairs"], 0)
        self.assertEqual(audit["summary"]["curated_excluded_pairs"], 1)
        self.assertEqual(audit["impure_pairs"], [])

    def test_audit_expect_accepts_a_faithful_copy_and_reports_drift(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "corpus"
            source.mkdir()
            impure = pair(
                "drifting",
                chosen_state={"sim_or_real": "designed", "domain": "a"},
                rejected_state={"sim_or_real": "designed", "domain": "b"},
            )
            write_jsonl(source / "preferences.jsonl", [pair("clean"), impure])

            status, stdout, _ = run_cli("audit", str(source), "--json")
            self.assertEqual(status, 0)
            expected = root / "audit.json"
            expected.write_text(stdout, encoding="utf-8")

            status, _, stderr = run_cli("audit", str(source), "--json", "--expect", str(expected))
            self.assertEqual(status, 0, stderr)

            drifted = json.loads(expected.read_text(encoding="utf-8"))
            drifted["impure_pairs"][0]["reason_codes"] = ["SOMETHING_ELSE"]
            drifted["summary"]["state_divergent_pairs"] = 99
            expected.write_text(json.dumps(drifted), encoding="utf-8")
            status, _, stderr = run_cli("audit", str(source), "--json", "--expect", str(expected))
            self.assertEqual(status, 1)
            self.assertIn("summary.state_divergent_pairs", stderr)
            self.assertIn("reason_codes", stderr)

    def test_audit_expect_names_pairs_present_on_only_one_side(self):
        actual = {
            "schema_version": curate_preferences.AUDIT_SCHEMA_VERSION,
            "audit": curate_preferences.AUDIT_NAME,
            "transform": {"name": "t", "version": "1"},
            "summary": {"impure_pairs": 1},
            "impure_pairs": [{"source_path": "a.jsonl", "source_line": 2}],
        }
        expected = copy.deepcopy(actual)
        expected["impure_pairs"] = [{"source_path": "a.jsonl", "source_line": 10}]
        differences = curate_preferences.audit_differences(expected, actual)
        self.assertIn("a.jsonl:10: audited impure pair is absent from this scan", differences)
        self.assertIn("a.jsonl:2: impure pair is absent from the audit", differences)
        self.assertEqual(
            curate_preferences.audit_differences("not-a-document", actual),
            ["expected audit document is not a JSON object"],
        )

    def test_audit_expect_detects_drift_in_a_retained_pair(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "preferences.jsonl"
            write_jsonl(source, [pair("retained")])
            expected = curate_preferences.build_audit(curate_preferences.curate_source(source))

            changed = pair("retained-renamed")
            write_jsonl(source, [changed])
            actual = curate_preferences.build_audit(curate_preferences.curate_source(source))

        self.assertEqual(expected["summary"], actual["summary"])
        self.assertEqual(expected["impure_pairs"], actual["impure_pairs"])
        differences = curate_preferences.audit_differences(expected, actual)
        self.assertTrue(
            any("preferences.jsonl: source_file_sha256" in item for item in differences)
        )

    def test_audit_markdown_and_human_output(self):
        status, markdown, _ = run_cli("audit", str(PURITY_FIXTURES), "--markdown")
        self.assertEqual(status, 0)
        self.assertIn("| Impure pairs (either field diverges) | 19 |", markdown)

        status, human, _ = run_cli("audit", str(PURITY_FIXTURES))
        self.assertEqual(status, 0)
        self.assertIn("Impure pairs: 19 (state 17, proposal 14, proposal only 2)", human)
        self.assertIn("batch-r05.jsonl:2", human)
        self.assertIn("[proposed_action]", human)

    def test_reconcile_accepts_a_byte_identical_copy(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            copied = root / "copy"
            copied.mkdir()
            for path in sorted(PURITY_FIXTURES.glob("*.jsonl")):
                (copied / path.name).write_bytes(path.read_bytes())
            status, stdout, _ = run_cli("reconcile", str(PURITY_FIXTURES), str(copied))
            self.assertEqual(status, 0)
            self.assertIn("scan identically", stdout)

    def test_reconcile_detects_whole_file_byte_drift(self):
        clean_line = json.dumps(pair("clean"), sort_keys=True)
        ordinary_a = json.dumps({"id": "metadata", "note": "a"}, sort_keys=True)
        ordinary_b = json.dumps({"id": "metadata", "note": "b"}, sort_keys=True)
        cases = {
            "skipped-record": (
                f"{ordinary_a}\n{clean_line}\n".encode(),
                f"{ordinary_b}\n{clean_line}\n".encode(),
            ),
            "line-ending": (
                f"{ordinary_a}\n{clean_line}\n".encode(),
                f"{ordinary_a}\r\n{clean_line}\r\n".encode(),
            ),
            "trailing-blank": (
                f"{ordinary_a}\n{clean_line}\n".encode(),
                f"{ordinary_a}\n{clean_line}\n\n".encode(),
            ),
        }
        for name, (first_payload, second_payload) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                first, second = root / "first", root / "second"
                first.mkdir()
                second.mkdir()
                (first / "preferences.jsonl").write_bytes(first_payload)
                (second / "preferences.jsonl").write_bytes(second_payload)

                differences = curate_preferences.reconcile_runs(
                    curate_preferences.curate_source(first),
                    curate_preferences.curate_source(second),
                )

                self.assertEqual(differences["coverage"], [])
                self.assertEqual(differences["decisions"], [])
                self.assertTrue(
                    any("source_file_sha256" in item for item in differences["payload"])
                )

    def test_inventory_covers_non_preference_only_and_quarantine_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "metadata.jsonl").write_text('{"note":"only metadata"}\n')
            write_jsonl(
                root / "batch-r723.jsonl",
                [leftover_mill_episode("dbc-r723-audit-leftover"), pair("clean")],
            )

            run = curate_preferences.curate_source(root)
            audit = curate_preferences.build_audit(run)
            differences = curate_preferences.reconcile_runs(run, run)

        self.assertEqual(
            [entry["source_path"] for entry in run.source_files],
            ["batch-r723.jsonl", "metadata.jsonl"],
        )
        self.assertEqual(audit["summary"]["impure_pairs"], 0)
        self.assertEqual(len(audit["source_files"]), 2)
        self.assertEqual(differences, {"coverage": [], "decisions": [], "payload": []})

    def test_reconcile_separates_coverage_decision_and_payload_drift(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first, second = root / "first", root / "second"
            first.mkdir()
            second.mkdir()
            clean = pair("clean")
            impure = pair(
                "impure",
                chosen_state={"sim_or_real": "designed", "domain": "a"},
                rejected_state={"sim_or_real": "designed", "domain": "b"},
            )
            write_jsonl(first / "preferences.jsonl", [clean, impure, clean])
            # Same first line by verdict but different bytes, a different
            # verdict on line 2, and one line fewer.
            renamed = copy.deepcopy(clean)
            renamed["id"] = "clean-renamed"
            write_jsonl(second / "preferences.jsonl", [renamed, clean])

            status, stdout, _ = run_cli("reconcile", str(first), str(second), "--json")
            self.assertEqual(status, 1)
            report = json.loads(stdout)
            self.assertEqual(
                report["difference_count"],
                sum(len(values) for values in report["differences"].values()),
            )
            coverage = "\n".join(report["differences"]["coverage"])
            decisions = "\n".join(report["differences"]["decisions"])
            payload = "\n".join(report["differences"]["payload"])
            self.assertIn("preferences.jsonl:3", coverage)
            self.assertIn("summary.preference_records", coverage)
            self.assertIn("preferences.jsonl:2", decisions)
            self.assertIn("same_state", decisions)
            self.assertIn("preferences.jsonl:1", payload)
            self.assertIn("source_record_id", payload)


class MarkdownAuditEscaping(unittest.TestCase):
    """`record_id` is audited JSON, not a constrained internal enum."""

    def render(self, **overrides):
        pair_row = {
            "record_id": "plain-id",
            "source_path": "preferences.jsonl",
            "source_line": 1,
            "same_state": False,
            "same_proposed_action": True,
            "action": "excluded",
            "reason_codes": ["STATE_CONTEXT_DIVERGES"],
        }
        pair_row.update(overrides)
        audit = {
            "summary": {
                "preference_pairs": 1,
                "state_divergent_pairs": 1,
                "proposed_action_divergent_pairs": 0,
                "impure_pairs": 1,
                "state_only_divergent_pairs": 1,
                "proposed_action_only_divergent_pairs": 0,
                "both_context_fields_divergent_pairs": 0,
                "context_undetermined_pairs": 0,
                "curated_retained_pairs": 0,
                "curated_excluded_pairs": 1,
                "retained_context_purity_pct": 0.0,
            },
            "impure_pairs": [pair_row],
        }
        return curate_preferences.render_audit_markdown(audit)

    def body_rows(self, rendered):
        marker = "| Pair | Source |"
        start = rendered.index(marker)
        rows = rendered[start:].splitlines()
        # Drop the header and its delimiter row.
        return rows[2:]

    def delimiter_pipes(self, row):
        """Pipes a GFM reader treats as cell delimiters.

        A backslash escapes the character after it, so ``\\|`` is a literal
        pipe but ``\\\\|`` is an escaped backslash followed by a delimiter
        that opens a new cell.
        """

        count = 0
        index = 0
        while index < len(row):
            if row[index] == "\\":
                index += 2
                continue
            if row[index] == "|":
                count += 1
            index += 1
        return count

    def cell_count(self, row):
        """Cells a Markdown reader sees: an escaped ``\\|`` is not a delimiter."""

        return row.replace("\\|", "").count("|") - 1

    def test_a_pipe_in_a_record_id_cannot_open_a_new_column(self):
        rendered = self.render(record_id="evil|injected|columns")
        rows = self.body_rows(rendered)

        self.assertEqual(len(rows), 1)
        self.assertEqual(self.cell_count(rows[0]), 6)
        self.assertIn("\\|", rows[0])

    def test_a_newline_in_a_record_id_cannot_inject_a_row(self):
        rendered = self.render(
            record_id="hidden\n| forged | preferences.jsonl:9 | yes | yes | retained | none"
        )
        rows = self.body_rows(rendered)

        self.assertEqual(len(rows), 1)
        self.assertEqual(self.cell_count(rows[0]), 6)
        # The forged text is still shown, but flattened into the one cell it
        # belongs to instead of becoming a row of its own.
        self.assertIn("hidden", rows[0])
        self.assertIn("forged", rows[0])

    def test_a_backtick_cannot_break_out_of_the_code_span(self):
        rendered = self.render(record_id="a`b")
        rows = self.body_rows(rendered)

        self.assertEqual(len(rows), 1)
        self.assertIn("``a`b``", rows[0])

    def test_a_source_path_and_reason_code_are_escaped_too(self):
        rendered = self.render(
            source_path="run|forged.jsonl", reason_codes=["A|B"]
        )
        rows = self.body_rows(rendered)

        self.assertEqual(len(rows), 1)
        self.assertEqual(self.cell_count(rows[0]), 6)

    def test_plain_values_render_exactly_as_before(self):
        rows = self.body_rows(self.render())

        self.assertEqual(
            rows[0],
            "| `plain-id` | `preferences.jsonl:1` | no | yes | excluded "
            "| `STATE_CONTEXT_DIVERGES` |",
        )


    def test_a_backslash_before_a_pipe_cannot_open_a_new_column(self):
        # Escaping only the pipe emits ``\\|``, whose first backslash escapes
        # the second and leaves the pipe free to act as a delimiter again.
        rendered = self.render(record_id="x\\|forged")
        rows = self.body_rows(rendered)

        self.assertEqual(len(rows), 1)
        self.assertEqual(self.delimiter_pipes(rows[0]), 7)

    def test_a_run_of_backslashes_before_a_pipe_cannot_open_a_new_column(self):
        rendered = self.render(source_path="run\\\\|forged.jsonl")
        rows = self.body_rows(rendered)

        self.assertEqual(len(rows), 1)
        self.assertEqual(self.delimiter_pipes(rows[0]), 7)

    def test_a_plain_row_has_exactly_the_six_documented_cells(self):
        rows = self.body_rows(self.render())

        self.assertEqual(self.delimiter_pipes(rows[0]), 7)

    def test_a_zero_record_id_is_rendered_not_reported_as_missing(self):
        rows = self.body_rows(self.render(record_id=0))

        self.assertIn("`0`", rows[0])
        self.assertNotIn("no record id", rows[0])

    def test_a_false_record_id_is_rendered_not_reported_as_missing(self):
        rows = self.body_rows(self.render(record_id=False))

        self.assertIn("`False`", rows[0])
        self.assertNotIn("no record id", rows[0])

    def test_an_empty_record_id_is_rendered_not_reported_as_missing(self):
        rows = self.body_rows(self.render(record_id=""))

        self.assertNotIn("no record id", rows[0])

    def test_only_a_null_record_id_is_reported_as_missing(self):
        rows = self.body_rows(self.render(record_id=None))

        self.assertIn("_(no record id)_", rows[0])


class FalseyRecordIdsInTheTextRenderers(unittest.TestCase):
    """``0`` and ``false`` are record ids; only ``null`` is a missing one."""

    def audit_text(self, record_id):
        audit = {
            "summary": {
                "preference_pairs": 1,
                "impure_pairs": 1,
                "state_divergent_pairs": 1,
                "proposed_action_divergent_pairs": 0,
                "proposed_action_only_divergent_pairs": 0,
                "curated_retained_pairs": 0,
                "retained_context_purity_pct": 0.0,
            },
            "impure_pairs": [
                {
                    "source_path": "batch-r05.jsonl",
                    "source_line": 1,
                    "record_id": record_id,
                    "action": "excluded",
                    "divergent_context_fields": ["state"],
                    "reason_codes": ["STATE_CONTEXT_DIVERGES"],
                }
            ],
        }
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            curate_preferences._print_audit_text(audit)
        return out.getvalue()

    def human_text(self, record_id):
        run = curate_preferences.CurationRun(
            records=(),
            manifest=(
                {
                    "source_path": "batch-r05.jsonl",
                    "source_line": 1,
                    "source_record_id": record_id,
                    "action": "excluded",
                    "reason_codes": ["STATE_CONTEXT_DIVERGES"],
                },
            ),
            summary={
                "preference_records": 1,
                "impure_pairs": 1,
                "state_divergent_pairs": 1,
                "proposed_action_divergent_pairs": 0,
                "proposed_action_only_divergent_pairs": 0,
                "retained_pairs": 0,
                "excluded_pairs": 1,
                "leftover_mill_records": 0,
                "retained_context_purity_pct": 0.0,
            },
        )
        return curate_preferences._render_human(run)

    def test_the_audit_text_renderer_keeps_a_zero_record_id(self):
        self.assertIn("batch-r05.jsonl:1 0:", self.audit_text(0))

    def test_the_audit_text_renderer_keeps_a_false_record_id(self):
        self.assertIn("batch-r05.jsonl:1 False:", self.audit_text(False))

    def test_the_audit_text_renderer_still_marks_a_null_record_id(self):
        self.assertIn("<no-id>", self.audit_text(None))

    def test_the_human_renderer_keeps_a_zero_record_id(self):
        self.assertIn("batch-r05.jsonl:1 0:", self.human_text(0))

    def test_the_human_renderer_keeps_a_false_record_id(self):
        self.assertIn("batch-r05.jsonl:1 False:", self.human_text(False))

    def test_the_human_renderer_still_marks_a_null_record_id(self):
        self.assertIn("<no-id>", self.human_text(None))


if __name__ == "__main__":
    unittest.main()
