#!/usr/bin/env python3
"""VSET validate_vset.py subprocess CLI tests."""

from __future__ import annotations

import json
import sys
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
