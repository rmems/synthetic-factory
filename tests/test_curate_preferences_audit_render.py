#!/usr/bin/env python3
"""How the audit renders a value it did not choose.

``record_id``, ``source_path`` and the reason codes come from source JSONL,
not from a constrained internal enum. Rendering them is therefore a security
boundary as much as a formatting one: a crafted value must not be able to add
table columns, inject a row, or hide a record from the published evidence,
and an ordinary value must come back out exactly as it went in.
"""

import contextlib
import io
import re
import unittest

import curate_preferences  # noqa: E402


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

    def code_span_text(self, cell):
        """The text a CommonMark reader shows for a code-span cell."""

        match = re.fullmatch(r"(`+)(.*)\1", cell.strip())
        self.assertIsNotNone(match, f"not a well-formed code span: {cell!r}")
        content = match.group(2)
        # One leading and one trailing space are removed when both are there,
        # unless the content is nothing but spaces.
        if not content.strip(" "):
            return content
        if content.startswith(" ") and content.endswith(" "):
            return content[1:-1]
        return content

    def id_cell(self, rendered):
        return self.body_rows(rendered)[0].split("|")[1]

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


    def test_a_padded_record_id_survives_code_span_normalization(self):
        # A reader strips one space from each side of a code span, so " x "
        # and "x" would otherwise be shown as the same id.
        self.assertEqual(self.code_span_text(self.id_cell(self.render(record_id=" x "))), " x ")

    def test_a_leading_space_record_id_is_preserved(self):
        self.assertEqual(self.code_span_text(self.id_cell(self.render(record_id=" x"))), " x")

    def test_an_all_space_record_id_is_preserved(self):
        self.assertEqual(self.code_span_text(self.id_cell(self.render(record_id="   "))), "   ")

    def test_a_backtick_padded_record_id_is_still_preserved(self):
        self.assertEqual(self.code_span_text(self.id_cell(self.render(record_id="`a`"))), "`a`")

    def test_an_empty_record_id_is_shown_explicitly_not_as_an_empty_span(self):
        row = self.body_rows(self.render(record_id=""))[0]

        # An empty code span cannot be written in CommonMark at all, so the
        # empty id has to be stated rather than fenced.
        self.assertIn("_(empty)_", row)
        self.assertNotIn("no record id", row)
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
