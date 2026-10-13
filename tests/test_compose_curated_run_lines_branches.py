"""Fail-closed branches of compose JSONL framing and manifest accounting."""

from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
for _path in (TESTS, TESTS.parent / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import compose_curated_run_lines as lines
from compose_contract import ComposeDecision, ComposeError

RELATIVE = "f/batch-r01.jsonl"
SENTINEL = ComposeDecision("excluded", None, ("sentinel",), (), None, None)


def _finding():
    return types.SimpleNamespace(
        reason_codes=("mill.foreign_family",), as_dict=lambda: {"family": "foreign"}
    )


def _physical_line(mill_findings) -> lines.PhysicalSourceLine:
    context = lines.SourceLineContext(RELATIVE, 2, "0" * 64, None, [], mill_findings)
    return lines.PhysicalSourceLine(b"{}", context)


class FramingTests(unittest.TestCase):
    def test_unknown_terminator_is_refused(self):
        with self.assertRaises(ComposeError) as caught:
            lines.jsonl_terminator_text(b"\r")

        self.assertEqual(str(caught.exception), "JSONL terminator must be LF, CRLF, or empty")

    def test_known_terminators_decode_exactly(self):
        decoded = [lines.jsonl_terminator_text(item) for item in (b"", b"\n", b"\r\n")]

        self.assertEqual(decoded, ["", "\n", "\r\n"])

    def test_only_a_terminal_cr_is_removed(self):
        self.assertEqual(lines.without_terminal_cr(b"a\rb\r"), b"a\rb")
        self.assertEqual(lines.without_terminal_cr(b"a\rb"), b"a\rb")


class OutputIdTests(unittest.TestCase):
    def test_missing_output_id_claims_nothing(self):
        state = lines.ComposeRunState()

        lines.claim_output_id(state, None, f"{RELATIVE}:1")

        self.assertEqual(state.emitted_ids, {})

    def test_colliding_output_id_is_refused(self):
        state = lines.ComposeRunState()
        lines.claim_output_id(state, "rec-1", f"{RELATIVE}:1")

        with self.assertRaises(ComposeError) as caught:
            lines.claim_output_id(state, "rec-1", f"{RELATIVE}:2")

        self.assertEqual(
            str(caught.exception),
            f"canonical ID collision 'rec-1': {RELATIVE}:1 and {RELATIVE}:2",
        )


class MillQuarantineTests(unittest.TestCase):
    def test_foreign_mill_finding_becomes_a_source_exclusion(self):
        decision = lines.mill_quarantined_decision(_finding())

        self.assertEqual(
            (decision.action, decision.reason_codes), ("excluded", ("mill.foreign_family",))
        )
        self.assertEqual(decision.stages[0]["classification"], "foreign_mill_quarantined")
        self.assertEqual(decision.stages[0]["detail"], {"family": "foreign"})

    def test_line_with_a_finding_is_quarantined_without_composition(self):
        services = types.SimpleNamespace(compose_source_line=mock.Mock())
        hooks = types.SimpleNamespace(mill_quarantined_decision=mock.Mock(return_value=SENTINEL))
        finding = _finding()

        decision = lines.line_decision(
            lines.ComposeRunState(), _physical_line({(RELATIVE, 2): finding}), services, hooks
        )

        self.assertIs(decision, SENTINEL)
        hooks.mill_quarantined_decision.assert_called_once_with(finding)
        services.compose_source_line.assert_not_called()

    def assert_composed(self, mill_findings) -> None:
        services = types.SimpleNamespace(compose_source_line=mock.Mock(return_value=SENTINEL))
        hooks = types.SimpleNamespace(mill_quarantined_decision=mock.Mock())

        decision = lines.line_decision(
            lines.ComposeRunState(), _physical_line(mill_findings), services, hooks
        )

        self.assertIs(decision, SENTINEL)
        hooks.mill_quarantined_decision.assert_not_called()

    def test_line_without_a_finding_is_composed(self):
        self.assert_composed({(RELATIVE, 1): _finding()})

    def test_run_without_a_mill_index_is_composed(self):
        self.assert_composed(None)


if __name__ == "__main__":
    unittest.main()
