#!/usr/bin/env python3
"""Hopper CLI: self-check, generate, and coded destination refusals."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hopper_test_support import CATALOG, FIXTURE, G46C_SLUG, REPO  # noqa: E402

from hopper.cli import run
from hopper.plants import DEFAULT_CATALOG_DIR


class HopperCliTests(unittest.TestCase):
    def test_default_catalog_is_shipped(self):
        self.assertEqual(DEFAULT_CATALOG_DIR, CATALOG)

    def test_self_check_json(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run(["self-check", "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["pairs"], 76)
        self.assertEqual(payload["plants"], 152)
        self.assertIn("g46c", payload["waves"])

    def test_generate_one_g46c_slug(self):
        import io
        from contextlib import redirect_stdout
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "fresh"
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = run([
                    "generate", "--out", str(out), "--wave", "g46c",
                    "--slug", G46C_SLUG, "--json",
                ])
            self.assertEqual(code, 0)
            payload = json.loads(buf.getvalue())
            self.assertEqual(payload["pairs"], 1)
            batch = (out / "search-index-rebuild-factory" / "batch-r50.jsonl").read_text(encoding="utf-8")
            self.assertEqual(batch, (FIXTURE / "g46c-zombodb.batch.jsonl").read_text(encoding="utf-8"))

    def test_generate_refuses_existing_out(self):
        import io
        from contextlib import redirect_stdout
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "exists"
            out.mkdir()
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = run(["generate", "--out", str(out), "--json"])
            self.assertEqual(code, 2)
            payload = json.loads(buf.getvalue())
            self.assertEqual(payload["status"], "refused")
            self.assertEqual(payload["code"], "DESTINATION_EXISTS")

    def test_generate_refuses_raw_alias(self):
        import io
        from contextlib import redirect_stdout
        raw = REPO / "outputs" / "raw" / "hopper-cli-should-refuse"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run(["generate", "--out", str(raw), "--json"])
        self.assertEqual(code, 2)
        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["status"], "refused")
        self.assertEqual(payload["code"], "DESTINATION_UNDER_RAW")

    def test_unknown_slug_refused(self):
        import io
        from contextlib import redirect_stdout
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "fresh"
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = run(["generate", "--out", str(out), "--slug", "no-such-slug", "--json"])
            self.assertEqual(code, 2)
            payload = json.loads(buf.getvalue())
            self.assertEqual(payload["code"], "UNKNOWN_SLUG")


if __name__ == "__main__":
    unittest.main()
