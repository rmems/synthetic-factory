#!/usr/bin/env python3
"""VSET validate_vset.py subprocess CLI tests."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from vset_testutil import ACCEPT, MANIFEST, PACK, REJECT, cli as _cli  # noqa: E402

class ValidateVsetCliTests(unittest.TestCase):
    def test_accept_directory_exits_zero(self):
        result = _cli(str(ACCEPT))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])

    def test_reject_directory_exits_nonzero(self):
        result = _cli(str(REJECT))
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("ERROR:", result.stderr)

    def test_oracle_cli_validates_the_accepted_issue_patch(self):
        result = _cli(
            "--oracle",
            "--pack",
            str(PACK),
            str(ACCEPT / "issue-patch-validated.json"),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["records"][0]["oracle_execution"]["hidden_ok"])

    def test_manifest_cli_exits_zero(self):
        result = _cli("--manifest", str(MANIFEST))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["ok"])


class PackOptionSurfaceTests(unittest.TestCase):
    """--pack must never look like it participated when it cannot."""

    def test_pack_without_oracle_is_rejected(self):
        result = _cli(str(ACCEPT), "--pack", str(PACK))
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("--pack requires --oracle", result.stderr)

    def test_pack_with_manifest_is_rejected(self):
        result = _cli("--manifest", str(MANIFEST), "--pack", str(PACK))
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("--pack requires --oracle", result.stderr)

    def test_pack_help_does_not_promise_a_default(self):
        result = _cli("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("defaults next to fixtures", result.stdout)
        self.assertIn("required with --oracle", result.stdout)


class UnreadableInputTests(unittest.TestCase):
    """A file we cannot decode is a reported record failure, not a crash."""

    def _broken_dir(self) -> tempfile.TemporaryDirectory:
        tmp = tempfile.TemporaryDirectory(prefix="vset-cli-")
        root = Path(tmp.name)
        shutil.copy(ACCEPT / "issue-patch-validated.json", root / "aa-good.json")
        (root / "yy-not-json.json").write_text("{not json", encoding="utf-8")
        (root / "zz-not-utf8.json").write_bytes(b"\xff\xfe\x00{")
        return tmp

    def test_unreadable_record_does_not_abort_the_directory_run(self):
        with self._broken_dir() as name:
            result = _cli(name)
        self.assertEqual(result.returncode, 1, result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        by_name = {Path(item["path"]).name: item for item in payload["records"]}
        self.assertEqual(
            sorted(by_name), ["aa-good.json", "yy-not-json.json", "zz-not-utf8.json"]
        )
        self.assertTrue(by_name["aa-good.json"]["ok"])
        for broken in ("yy-not-json.json", "zz-not-utf8.json"):
            with self.subTest(broken=broken):
                self.assertEqual(
                    by_name[broken]["reason_codes"], ["vset.record_not_object"]
                )

    def test_unreadable_manifest_is_a_reason_code_not_a_traceback(self):
        with tempfile.TemporaryDirectory(prefix="vset-cli-") as name:
            path = Path(name) / "manifest.json"
            path.write_text("{not json", encoding="utf-8")
            result = _cli("--manifest", str(path))
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(
            json.loads(result.stdout)["reason_codes"], ["vset.record_not_object"]
        )
