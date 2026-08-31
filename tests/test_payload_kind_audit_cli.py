#!/usr/bin/env python3
"""CLI tests for the read-only payload-kind audit: --json, --expect, --markdown.

Split out of test_payload_kind_audit.py: this is the one cluster of tests that
drives payload_kind_audit.main() end to end (exit codes, stdout/stderr, the
--expect drift contract) rather than calling build_audit() directly.
"""

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from payload_kind_audit_fixtures import REPO, _episode, _step, _write_corpus  # noqa: E402

PIPELINES = REPO / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import payload_kind_audit  # noqa: E402


class PayloadKindAuditCLI(unittest.TestCase):
    """CLI plumbing: --json/--markdown output selection and --expect drift."""

    def _expect_against_mutated_audit(self, mutate):
        """Publish a fresh single-episode audit, corrupt its serialized JSON
        with ``mutate``, and run --expect against the result.

        Returns ``(exit code, stderr)`` so each caller still asserts its own
        drift-versus-input-error status and diagnostic explicitly.
        """
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            _write_corpus(directory, {"episodes.jsonl": [_episode([])]})
            published = payload_kind_audit.build_audit(directory)
            expected = directory / "audit.json"
            expected.write_text(mutate(json.dumps(published)), encoding="utf-8")
            err = io.StringIO()
            with redirect_stderr(err), redirect_stdout(io.StringIO()):
                code = payload_kind_audit.main([str(directory), "--expect", str(expected)])
        return code, err.getvalue()

    def test_expect_rejects_bool_int_type_drift(self):
        code, err = self._expect_against_mutated_audit(
            lambda text: text.replace('"records": 1', '"records": true', 1)
        )
        self.assertEqual(code, 1)
        self.assertIn("summary differs from the published audit", err)

    def test_documented_json_flag_is_an_explicit_alias_for_the_default(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            _write_corpus(directory, {"episodes.jsonl": [_episode([])]})
            default_out = io.StringIO()
            with redirect_stdout(default_out):
                self.assertEqual(payload_kind_audit.main([str(directory)]), 0)
            explicit_out = io.StringIO()
            with redirect_stdout(explicit_out):
                self.assertEqual(payload_kind_audit.main([str(directory), "--json"]), 0)
        self.assertEqual(default_out.getvalue(), explicit_out.getvalue())

    def test_expect_accepts_a_faithful_audit_and_names_drift(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            _write_corpus(
                directory,
                {"episodes.jsonl": [_episode([_step(1, thought="t")])]},
            )
            audit = payload_kind_audit.build_audit(directory)
            faithful = directory / "audit.json"
            faithful.write_text(json.dumps(audit), encoding="utf-8")

            out = io.StringIO()
            with redirect_stdout(out):
                code = payload_kind_audit.main([str(directory), "--expect", str(faithful)])
            self.assertEqual(code, 0, out.getvalue())

            drifted = dict(audit)
            drifted["summary"] = dict(audit["summary"], records=99)
            stale = directory / "stale.json"
            stale.write_text(json.dumps(drifted), encoding="utf-8")

            err = io.StringIO()
            with redirect_stderr(err), redirect_stdout(io.StringIO()):
                code = payload_kind_audit.main([str(directory), "--expect", str(stale)])
            self.assertEqual(code, 1)
            self.assertIn("summary differs from the published audit", err.getvalue())

    def test_expect_reaudits_the_named_snapshot_not_later_appends(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            _write_corpus(
                directory,
                {"episodes.jsonl": [_episode([_step(1, thought="published")])]},
            )
            published = payload_kind_audit.build_audit(directory)
            expected = directory / "audit.json"
            expected.write_text(json.dumps(published), encoding="utf-8")

            _write_corpus(
                directory,
                {"batch-r10.jsonl": [_episode([_step(1, thought="later")])]},
            )
            self.assertEqual(payload_kind_audit.build_audit(directory)["summary"]["records"], 2)
            out = io.StringIO()
            with redirect_stdout(out):
                code = payload_kind_audit.main([str(directory), "--expect", str(expected)])
            self.assertEqual(code, 0, out.getvalue())

    def test_expect_rejects_unsafe_or_duplicate_snapshot_names(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            _write_corpus(directory, {"episodes.jsonl": [_episode([])]})
            base = payload_kind_audit.build_audit(directory)
            for paths in (("episodes.jsonl", "episodes.jsonl"), ("../escape.jsonl",)):
                with self.subTest(paths=paths):
                    published = dict(base)
                    published["files"] = [{"path": path} for path in paths]
                    expected = directory / "audit.json"
                    expected.write_text(json.dumps(published), encoding="utf-8")
                    err = io.StringIO()
                    with redirect_stderr(err):
                        code = payload_kind_audit.main([str(directory), "--expect", str(expected)])
                    self.assertEqual(code, 2)
                    self.assertIn("payload-kind audit failed", err.getvalue())

    def test_snapshot_name_type_errors_are_controlled(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            _write_corpus(directory, {"episodes.jsonl": [_episode([])]})
            with self.assertRaises(payload_kind_audit.PayloadKindAuditError) as caught:
                payload_kind_audit.build_audit(directory, payload_names=[[]])
        self.assertIn("unsafe snapshot payload name", str(caught.exception))

    def test_expect_rejects_non_standard_json_constants_as_input_errors(self):
        code, err = self._expect_against_mutated_audit(
            lambda text: text.replace('"records": 1', '"records": NaN', 1)
        )
        self.assertEqual(code, 2)
        self.assertIn("non-standard JSON constant", err)

    def test_expect_rejects_duplicate_object_keys(self):
        code, err = self._expect_against_mutated_audit(
            lambda text: text.replace("{", '{"summary":{"records":999},', 1)
        )
        self.assertEqual(code, 2)
        self.assertIn("duplicate JSON object key", err)

    def test_expect_rejects_numeric_literals_that_overflow_to_infinity(self):
        code, err = self._expect_against_mutated_audit(
            lambda text: text.replace('"records": 1', '"records": 1e400', 1)
        )
        self.assertEqual(code, 2)
        self.assertIn("outside the finite float range", err)

    def test_expect_rejects_excessively_nested_json_as_an_input_error(self):
        depth = 200000
        nested = "[" * depth + "]" * depth
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            _write_corpus(directory, {"episodes.jsonl": [_episode([])]})
            expected = directory / "audit.json"
            expected.write_text(nested, encoding="utf-8")
            err = io.StringIO()
            with redirect_stderr(err), redirect_stdout(io.StringIO()):
                code = payload_kind_audit.main([str(directory), "--expect", str(expected)])
        self.assertEqual(code, 2)
        self.assertIn("cannot read", err.getvalue())

    def _expect_document_with_card_disclosure(self, directory, markdown_literal):
        """Write an --expect file whose supplementary card_disclosure holds one
        raw JSON string literal, and return its path.

        The literal is injected as source text because a lone surrogate cannot
        be written through Python's UTF-8 encoder at all - which is precisely
        the input the corpus parser rejects and this parser must too.
        """
        _write_corpus(directory, {"episodes.jsonl": [_episode([])]})
        audit = payload_kind_audit.build_audit(directory)
        document = dict(audit)
        document["card_disclosure"] = {"markdown": "__PLACEHOLDER__"}
        serialized = json.dumps(document).replace('"__PLACEHOLDER__"', markdown_literal)
        expected = directory / "audit.json"
        expected.write_text(serialized, encoding="utf-8")
        return expected

    def test_expect_rejects_an_unpaired_surrogate_in_a_supplementary_field(self):
        """_drift only compares derived keys, so a malformed supplementary
        field would otherwise exit 0 while the corpus parser rejects the same
        string (Codex #74)."""
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            expected = self._expect_document_with_card_disclosure(
                directory, '"\\ud800"'
            )
            err = io.StringIO()
            with redirect_stderr(err), redirect_stdout(io.StringIO()):
                code = payload_kind_audit.main([str(directory), "--expect", str(expected)])
        self.assertEqual(code, 2)
        self.assertIn("cannot read", err.getvalue())
        self.assertIn("unpaired UTF-16 surrogate", err.getvalue())

    def test_expect_still_accepts_a_well_formed_supplementary_field(self):
        """Only the malformed string is refused; extra published context that
        no corpus scan can derive still passes the drift gate."""
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            expected = self._expect_document_with_card_disclosure(
                directory, '"| Source | Kind |"'
            )
            out = io.StringIO()
            with redirect_stdout(out):
                code = payload_kind_audit.main([str(directory), "--expect", str(expected)])
        self.assertEqual(code, 0, out.getvalue())


if __name__ == "__main__":
    unittest.main()
