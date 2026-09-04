#!/usr/bin/env python3
"""Exact export-member reads and their compatibility surface."""

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parents[0]
sys.path.insert(0, str(REPO / "pipelines"))

import export_members  # noqa: E402


class ExportMemberCompatibility(unittest.TestCase):
    def _assert_descriptor_resolves_hook_at_call_time(self, hook_name):
        class FacadeHookReached(Exception):
            pass

        payload = b'{"id":"one"}\n'
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            member = root / "manifest.jsonl"
            member.write_bytes(payload)
            summary = {
                "manifest": {
                    "path": member.name,
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "entries": 1,
                }
            }

            with mock.patch.object(
                export_members,
                hook_name,
                side_effect=FacadeHookReached,
            ):
                with self.assertRaises(FacadeHookReached):
                    export_members._authenticated_descriptor(root, summary, "manifest", member.name)

    def test_descriptor_authentication_resolves_facade_reader_at_call_time(self):
        self._assert_descriptor_resolves_hook_at_call_time("_read_exact_regular_file")

    def test_descriptor_authentication_resolves_facade_parser_at_call_time(self):
        self._assert_descriptor_resolves_hook_at_call_time("_lf_jsonl_documents")

    def test_reads_exact_lf_jsonl_through_the_export_hf_surface(self):
        payload = b'{"id":"one"}\n{"id":"two"}\n'
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            member = root / "member.jsonl"
            member.write_bytes(payload)

            path, captured = export_members._read_exact_regular_file(
                root, member.name, "curated payload"
            )

        self.assertEqual(path, member)
        self.assertEqual(captured, payload)
        self.assertEqual(
            export_members._lf_jsonl_documents(captured, member.name),
            [{"id": "one"}, {"id": "two"}],
        )

    def test_descriptor_authentication_rejects_duplicate_json_keys(self):
        payload = b'{"id":"one","id":"two"}\n'
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            member = root / "manifest.jsonl"
            member.write_bytes(payload)
            summary = {
                "manifest": {
                    "path": member.name,
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "entries": 1,
                }
            }

            with self.assertRaisesRegex(export_members.ExportError, "duplicate JSON object key"):
                export_members._authenticated_descriptor(root, summary, "manifest", member.name)

    def test_descriptor_digest_is_checked_before_parsing_member_json(self):
        payload = b"not-json\n"
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            member = root / "manifest.jsonl"
            member.write_bytes(payload)
            summary = {
                "manifest": {
                    "path": member.name,
                    "sha256": "0" * 64,
                    "entries": 1,
                }
            }

            with self.assertRaisesRegex(export_members.ExportError, "digest mismatch"):
                export_members._authenticated_descriptor(root, summary, "manifest", member.name)


if __name__ == "__main__":
    unittest.main()
