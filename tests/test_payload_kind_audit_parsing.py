#!/usr/bin/env python3
"""Fail-closed corpus-parsing tests for the read-only payload-kind audit.

Split out of test_payload_kind_audit.py: this concern is the walk from bytes
on disk to classified records — JSONL framing, strict JSON parsing, digests,
and unreadable inputs — every one of which must end in a controlled
PayloadKindAuditError rather than a guess or a traceback.
"""

import hashlib
import io
import json
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from payload_kind_audit_fixtures import REPO, _episode, _step  # noqa: E402
from payload_kind_audit_test_support import PayloadKindAuditCase  # noqa: E402

import payload_kind_audit  # noqa: E402


class PayloadKindParsing(PayloadKindAuditCase):
    """Ambiguous or unreadable input is a diagnostic, never a certified audit."""

    def test_unicode_line_separator_inside_json_string_is_not_a_record_boundary(self):
        with TemporaryDirectory() as raw:
            directory = Path(raw)
            record = _episode([_step(1)])
            record["goal"] = "first\u2028second"
            (directory / "episodes.jsonl").write_text(
                json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            audit = payload_kind_audit.build_audit(directory)
        self.assertEqual(audit["summary"]["records"], 1)

    def test_non_standard_json_constants_are_rejected(self):
        self._assert_rejects_raw_payload(
            "episodes.jsonl",
            '{"goal":"g","steps":[],"meta":{"score":NaN}}\n',
            "non-standard JSON constant",
        )

    def test_numeric_literals_that_overflow_to_infinity_are_rejected(self):
        self._assert_rejects_raw_payload(
            "episodes.jsonl",
            '{"id":1e400,"goal":"g","steps":[]}\n',
            "outside the finite float range",
        )

    def test_duplicate_object_keys_are_rejected(self):
        self._assert_rejects_raw_payload(
            "episodes.jsonl",
            '{"goal":"g","steps":"bad","steps":[]}\n',
            "duplicate JSON object key",
        )

    def test_unicode_whitespace_only_lines_are_rejected(self):
        self._assert_rejects_raw_payload(
            "episodes.jsonl",
            '{"goal":"g","steps":[]}\n\u00a0\n',
            "episodes.jsonl:2",
        )

    def test_a_malformed_line_fails_loudly_instead_of_being_skipped(self):
        self._assert_rejects_raw_payload(
            "batch-r02.jsonl",
            json.dumps(_episode([_step(1)])) + "\nnot json\n",
            "batch-r02.jsonl:2",
        )

    def test_a_non_object_record_is_rejected(self):
        self._assert_rejects_raw_payload(
            "batch-r02.jsonl", "[1, 2, 3]\n", "must be a JSON object"
        )

    def test_unpaired_surrogates_are_rejected(self):
        with TemporaryDirectory() as raw:
            directory = Path(raw)
            (directory / "episodes.jsonl").write_text(
                '{"id":"\\ud800","goal":"g","steps":[]}\n',
                encoding="utf-8",
            )
            with self.assertRaises(payload_kind_audit.PayloadKindAuditError) as caught:
                payload_kind_audit.build_audit(directory)
            err = io.StringIO()
            with redirect_stderr(err), redirect_stdout(io.StringIO()):
                code = payload_kind_audit.main([str(directory), "--markdown"])
        self.assertIn("unpaired UTF-16 surrogate", str(caught.exception))
        self.assertEqual(code, 2)
        self.assertIn("payload-kind audit failed", err.getvalue())

    def test_excessively_nested_json_is_a_controlled_audit_error(self):
        depth = 2000
        nested = "[" * depth + "]" * depth
        line = '{"goal":"g","steps":[],"meta":' + nested + "}"
        with TemporaryDirectory() as raw:
            directory = Path(raw)
            (directory / "episodes.jsonl").write_text(line + "\n", encoding="utf-8")
            with self.assertRaises(payload_kind_audit.PayloadKindAuditError) as caught:
                payload_kind_audit.build_audit(directory)
            err = io.StringIO()
            with redirect_stderr(err), redirect_stdout(io.StringIO()):
                code = payload_kind_audit.main([str(directory)])
        self.assertIn("episodes.jsonl:1", str(caught.exception))
        self.assertEqual(code, 2)
        self.assertIn("payload-kind audit failed", err.getvalue())

    def test_final_bare_cr_is_preserved_in_record_digest(self):
        record = b'{"goal":"g","steps":[]}'
        with TemporaryDirectory() as raw:
            directory = Path(raw)
            (directory / "episodes.jsonl").write_bytes(record + b"\r")
            audit = payload_kind_audit.build_audit(directory)
        self.assertEqual(
            audit["records"][0]["sha256"],
            hashlib.sha256(record + b"\r").hexdigest(),
        )

    def test_invalid_utf8_and_read_failures_are_controlled_audit_errors(self):
        with TemporaryDirectory() as raw:
            directory = Path(raw)
            payload = directory / "episodes.jsonl"
            payload.write_bytes(b'{"goal":"\xff","steps":[]}\n')
            with self.assertRaises(payload_kind_audit.PayloadKindAuditError) as caught:
                payload_kind_audit.build_audit(directory)
            self.assertIn("not valid UTF-8", str(caught.exception))

            payload.write_text(json.dumps(_episode([])) + "\n", encoding="utf-8")
            with patch.object(Path, "read_bytes", side_effect=OSError("denied")):
                with self.assertRaises(payload_kind_audit.PayloadKindAuditError) as caught:
                    payload_kind_audit.build_audit(directory)
            self.assertIn("cannot read payload", str(caught.exception))

    def test_empty_or_payload_free_corpora_are_rejected(self):
        for empty_file in (False, True):
            with self.subTest(empty_file=empty_file):
                with TemporaryDirectory() as raw:
                    directory = Path(raw)
                    if empty_file:
                        (directory / "episodes.jsonl").write_text("\n", encoding="utf-8")
                    with self.assertRaises(payload_kind_audit.PayloadKindAuditError) as caught:
                        payload_kind_audit.build_audit(directory)
                expected = "no auditable records" if empty_file else "no *.jsonl payloads"
                self.assertIn(expected, str(caught.exception))

    def test_a_payload_filename_that_is_not_utf8_is_a_controlled_input_error(self):
        """A POSIX filename is bytes; Python surrogate-escapes undecodable
        ones. That name reaches every row as source_file and would raise an
        uncaught UnicodeEncodeError inside sys.stdout.write after a successful
        scan, instead of the documented status 2 (Codex #74)."""
        with TemporaryDirectory() as raw:
            directory = Path(raw)
            name = "batch-\udcff.jsonl"
            try:
                (directory / name).write_text(
                    json.dumps(_episode([])) + "\n", encoding="utf-8"
                )
            except (OSError, UnicodeEncodeError) as exc:  # pragma: no cover
                self.skipTest(f"filesystem rejects undecodable names: {exc}")
            with self.assertRaises(payload_kind_audit.PayloadKindAuditError) as caught:
                payload_kind_audit.build_audit(directory)
        self.assertIn("payload filename is not valid UTF-8", str(caught.exception))

    def test_a_missing_corpus_directory_is_rejected(self):
        with self.assertRaises(payload_kind_audit.PayloadKindAuditError):
            payload_kind_audit.build_audit(REPO / "docs" / "no-such-corpus")


if __name__ == "__main__":
    unittest.main()
