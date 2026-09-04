#!/usr/bin/env python3
"""Focused contracts for the per-line compose run framing."""

import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parents[0]
sys.path.insert(0, str(REPO / "pipelines"))

from compose_curated_run_lines import jsonl_physical_lines  # noqa: E402


class ComposeRunLinesContract(unittest.TestCase):
    def test_physical_jsonl_framing_uses_lf_only(self):
        """Unicode separators remain payload bytes while CRLF loses only CR."""

        payload = b'"line\xe2\x80\xa8separator"\r\n{"second":true}\n'

        self.assertEqual(
            jsonl_physical_lines(payload),
            [b'"line\xe2\x80\xa8separator"', b'{"second":true}'],
        )


if __name__ == "__main__":
    unittest.main()
