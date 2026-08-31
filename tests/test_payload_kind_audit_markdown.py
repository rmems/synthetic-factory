#!/usr/bin/env python3
"""Markdown-rendering tests for the read-only payload-kind audit.

Split out of test_payload_kind_audit.py: this concern is the --markdown table
an operator pastes into a card — audited values must land there faithfully
(falsy values kept, containers as JSON) and inertly (table, link, emphasis,
and control characters cannot activate as Markdown or reach a terminal raw).
"""

import sys
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from payload_kind_audit_fixtures import _episode, _thalamic  # noqa: E402
from payload_kind_audit_test_support import PayloadKindAuditCase  # noqa: E402

import payload_kind_audit  # noqa: E402


def _row(**overrides):
    """One literal audit row; each test overrides only what it exercises."""
    row = {
        "source_file": "batch.jsonl",
        "source_line": 1,
        "kind": "thalamic",
        "id": "id-1",
        "supervisor_id": "gate-v1",
        "gate_decision": "MODIFY",
        "wraps_coding_episode": True,
        "coding_steps": 2,
    }
    row.update(overrides)
    return row


def _render(*rows):
    """Render literal rows without a corpus scan behind them."""
    return payload_kind_audit.render_markdown({"records": list(rows)})


# The audit-row field each _thalamic builder keyword lands on.
_GATE_FIELDS = {"supervisor": "supervisor_id", "decision": "gate_decision"}


class PayloadKindMarkdown(PayloadKindAuditCase):
    """The record table renders audited values faithfully and inertly."""

    def test_markdown_preserves_falsy_record_identifiers(self):
        for identifier in (0, False):
            with self.subTest(identifier=identifier):
                record = _episode([])
                record["id"] = identifier
                audit = self._audit_corpus({"episodes.jsonl": [record]})
                self.assertEqual(audit["records"][0]["id"], identifier)
                rendered = payload_kind_audit.render_markdown(audit)
                self.assertIn(f"| episode | `{identifier}` |", rendered)
        audit = self._audit_corpus({"episodes.jsonl": [_episode([])]})
        self.assertIsNone(audit["records"][0]["id"])
        self.assertIn("| episode | — |", payload_kind_audit.render_markdown(audit))

    def _assert_gate_cell_preserves_falsy(self, keyword, values, cell, none_cell):
        """A present-but-falsy gate value renders literally; only a missing
        one becomes the em-dash placeholder. Each caller names its builder
        keyword and the exact cells it expects."""
        field = _GATE_FIELDS[keyword]
        for value in values:
            with self.subTest(value=value):
                record = _thalamic("act-r02-001", _episode([]), **{keyword: value})
                audit = self._audit_corpus({"batch-r02.jsonl": [record]})
                self.assertEqual(audit["records"][0][field], value)
                self.assertIn(cell.format(value), payload_kind_audit.render_markdown(audit))
        record = _thalamic("act-r02-001", _episode([]), **{keyword: None})
        audit = self._audit_corpus({"batch-r02.jsonl": [record]})
        self.assertIsNone(audit["records"][0][field])
        self.assertIn(none_cell, payload_kind_audit.render_markdown(audit))

    def test_markdown_preserves_falsy_supervisor_ids(self):
        self._assert_gate_cell_preserves_falsy(
            "supervisor", (0, False), "| {} / MODIFY |", "| — / MODIFY |"
        )

    def test_markdown_preserves_falsy_gate_decisions(self):
        self._assert_gate_cell_preserves_falsy(
            "decision", (0, False, ""), "| gate-v1 / {} |", "| gate-v1 |"
        )

    def test_markdown_escapes_dynamic_table_values(self):
        rendered = _render(
            _row(
                source_file="batch|name.jsonl",
                id="id|`tick`\nnext",
                supervisor_id="gate|one",
                gate_decision="MODIFY\nNOW",
            )
        )
        self.assertIn("batch&#124;name.jsonl", rendered)
        # The backtick is escaped rather than passed through: inside the
        # <code> fallback the entity decodes to the same character, so the
        # rendered table is unchanged, but the source cannot open a code span.
        self.assertIn("id&#124;&#96;tick&#96;<br>next", rendered)
        self.assertIn("gate&#124;one / MODIFY<br>NOW", rendered)

    def test_markdown_escapes_link_and_image_syntax_in_gate_cells(self):
        rendered = _render(
            _row(
                supervisor_id="![tracker](https://example.test/pixel)",
                gate_decision="[click me](https://example.test/bad)",
            )
        )
        self.assertNotIn("![tracker](", rendered)
        self.assertNotIn("[click me](", rendered)
        self.assertIn("!&#91;tracker&#93;(https://example.test/pixel)", rendered)
        self.assertIn("&#91;click me&#93;(https://example.test/bad)", rendered)

    def test_markdown_escapes_emphasis_and_backticks_in_gate_cells(self):
        """A gate cell is plain table text, so Markdown syntax in a valid
        supervisor id or decision renders formatting instead of literal audit
        data (Codex #74)."""
        rendered = _render(_row(supervisor_id="**gate**", gate_decision="MOD`IFY`_now_"))
        self.assertNotIn("**gate**", rendered)
        self.assertNotIn("`IFY`", rendered)
        self.assertIn("&#42;&#42;gate&#42;&#42;", rendered)
        self.assertIn("MOD&#96;IFY&#96;&#95;now&#95;", rendered)

    def test_markdown_escapes_control_characters_in_gate_cells(self):
        """json.loads decodes an escaped C0 control into the raw byte, which
        html.escape leaves alone, so --markdown would emit it to a terminal
        and into card-ready text (Codex #74)."""
        record = _thalamic("act-r02-001", _episode([]), supervisor="gate\x1bv1")
        audit = self._audit_corpus({"batch-r02.jsonl": [record]})
        self.assertEqual(audit["records"][0]["supervisor_id"], "gate\x1bv1")
        rendered = payload_kind_audit.render_markdown(audit)
        self.assertNotIn("\x1b", rendered)
        self.assertIn("gate\\u001bv1", rendered)

    def test_markdown_escapes_control_characters_in_record_identifiers(self):
        rendered = _render(_row(id="id\x00one\x07two"))
        self.assertNotIn("\x00", rendered)
        self.assertNotIn("\x07", rendered)
        self.assertIn("id\\u0000one\\u0007two", rendered)

    def test_markdown_keeps_ordinary_text_unescaped(self):
        """The control-character pass must not disturb printable values."""
        rendered = _render(_row(id="act-r02-001"))
        self.assertIn("`act-r02-001`", rendered)
        self.assertIn("gate-v1 / MODIFY", rendered)

    def test_markdown_renders_an_empty_identifier_as_a_closed_code_element(self):
        """An empty string is an accepted legacy identifier, but wrapping it
        in backticks yields one uninterrupted two-backtick run — a code-span
        delimiter, not an empty span — so the table shows stray backticks or
        absorbs later content into a phantom span (Codex #74)."""
        record = _episode([])
        record["id"] = ""
        audit = self._audit_corpus({"episodes.jsonl": [record]})
        self.assertEqual(audit["records"][0]["id"], "")
        rendered = payload_kind_audit.render_markdown(audit)
        self.assertIn("| <code></code> |", rendered)
        self.assertNotIn("``", rendered)

    def test_markdown_renders_a_code_span_without_publishing_entities(self):
        """A code span already disables inline syntax, so escaping inside one
        would print the entity instead of the character the corpus holds."""
        rendered = _render(
            _row(
                kind="episode",
                id="id_with*stars[and]brackets",
                wraps_coding_episode=False,
                coding_steps=0,
            )
        )
        self.assertIn("`id_with*stars[and]brackets`", rendered)

    def test_markdown_renders_container_gate_metadata_as_json(self):
        """The decimal guard permits a container-valued emitted field, and the
        row carries it verbatim, so str() would publish a Python repr that
        differs from the corpus JSON (Codex #74)."""
        record = _thalamic(
            "act-r02-001", _episode([]), supervisor={"key": None, "flags": [True, 1]}
        )
        audit = self._audit_corpus({"batch-r02.jsonl": [record]})
        self.assertEqual(
            audit["records"][0]["supervisor_id"], {"key": None, "flags": [True, 1]}
        )
        rendered = payload_kind_audit.render_markdown(audit)
        self.assertNotIn("'key': None", rendered)
        self.assertIn('{"flags": &#91;true, 1&#93;, "key": null}', rendered)

    def test_markdown_renders_a_container_identifier_as_json(self):
        record = _episode([])
        record["id"] = ["a", None]
        audit = self._audit_corpus({"episodes.jsonl": [record]})
        rendered = payload_kind_audit.render_markdown(audit)
        self.assertNotIn("None", rendered)
        self.assertIn('`["a", null]`', rendered)


if __name__ == "__main__":
    unittest.main()
