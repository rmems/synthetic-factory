"""Shared TestCase base for the payload-kind audit test modules.

test_payload_kind_audit.py (classification), test_payload_kind_audit_identity.py,
test_payload_kind_audit_parsing.py, test_payload_kind_audit_decimal_guard.py,
and test_payload_kind_audit_markdown.py each cover one concern of
pipelines/payload_kind_audit.py. The corpus-directory boilerplate they share —
audit a synthetic corpus read-only, or prove one malformed corpus fails
closed — lives here so no concern module repeats it. Record builders stay in
payload_kind_audit_fixtures.py.
"""

from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from payload_kind_audit_fixtures import REPO, _write_corpus  # noqa: E402

PIPELINES = REPO / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import payload_kind_audit  # noqa: E402


class PayloadKindAuditCase(unittest.TestCase):
    """Corpus-directory helpers shared by the audit's concern test modules."""

    def _audit_corpus(self, files):
        """Audit one synthetic corpus and prove the audit never wrote to it."""
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            _write_corpus(directory, files)
            before = {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(directory.iterdir())
            }
            audit = payload_kind_audit.build_audit(directory)
            after = {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(directory.iterdir())
            }
            self.assertEqual(before, after, "the audit must never write to the corpus")
            return audit

    def _assert_rejects_corpus(self, files, *expected_substrings):
        """Assert build_audit fails closed on ``files``, naming each substring.

        Each caller still states its own records and expected diagnostics
        explicitly; only the tempdir/assertRaises boilerplate is shared.
        """
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            _write_corpus(directory, files)
            with self.assertRaises(payload_kind_audit.PayloadKindAuditError) as caught:
                payload_kind_audit.build_audit(directory)
        message = str(caught.exception)
        for expected in expected_substrings:
            self.assertIn(expected, message)
        return message

    def _assert_rejects_raw_payload(self, name, content, *expected_substrings):
        """Write one raw-text payload file and assert build_audit fails closed.

        For inputs no record builder can express — malformed JSON, non-standard
        constants, ambiguous framing — written to disk exactly as given.
        """
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            (directory / name).write_text(content, encoding="utf-8")
            with self.assertRaises(payload_kind_audit.PayloadKindAuditError) as caught:
                payload_kind_audit.build_audit(directory)
        message = str(caught.exception)
        for expected in expected_substrings:
            self.assertIn(expected, message)
        return message
