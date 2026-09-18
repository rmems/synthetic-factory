#!/usr/bin/env python3
"""Focused contracts for the per-line compose run framing."""

import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parents[0]
sys.path.insert(0, str(REPO / "pipelines"))

from compose_curated_run_lines import jsonl_framed_lines, jsonl_physical_lines  # noqa: E402


class ComposeRunLinesContract(unittest.TestCase):
    def test_physical_jsonl_framing_uses_lf_only(self):
        """Unicode separators remain payload bytes while CRLF loses only CR."""

        payload = b'"line\xe2\x80\xa8separator"\r\n{"second":true}\n'

        self.assertEqual(
            jsonl_physical_lines(payload),
            [b'"line\xe2\x80\xa8separator"', b'{"second":true}'],
        )

    def test_framed_jsonl_preserves_crlf_and_unterminated_final_record(self):
        payload = b'{"a":1}\r\n{"b":2}\n{"c":3}'
        self.assertEqual(
            jsonl_framed_lines(payload),
            [
                (b'{"a":1}', b"\r\n"),
                (b'{"b":2}', b"\n"),
                (b'{"c":3}', b""),
            ],
        )

    def test_unterminated_native_record_cannot_precede_another(self):
        from compose_contract import ComposeError
        from compose_curated_run_artifacts import write_emitted_records
        from compose_curated_run_context import ComposeRunState, SourceFileContext

        class Services:
            def write_new_text(self, *args, **kwargs):
                raise AssertionError("must not write unterminated middle records")

        with self.assertRaisesRegex(ComposeError, "unterminated"):
            write_emitted_records(
                ComposeRunState(),
                SourceFileContext("factory/a.jsonl", b"", object(), None),
                ['{"a":1}', '{"b":2}\n'],
                Services(),
            )


if __name__ == "__main__":
    unittest.main()
