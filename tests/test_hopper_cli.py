#!/usr/bin/env python3
"""Hopper CLI: self-check, generate, and coded destination refusals."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hopper_test_support import CATALOG, FIXTURE, G46C_SLUG, REPO  # noqa: E402

from hopper.cli import run
from hopper.plants import DEFAULT_CATALOG_DIR


def _run_json(argv):
    """Exit code and the one JSON object the CLI printed."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = run(argv)
    return code, json.loads(buf.getvalue())


def _generate_fresh(*selectors):
    with tempfile.TemporaryDirectory() as tmp:
        return _run_json(["generate", "--out", str(Path(tmp) / "fresh"), *selectors, "--json"])


class HopperCliTests(unittest.TestCase):
    def test_default_catalog_is_shipped(self):
        self.assertEqual(DEFAULT_CATALOG_DIR, CATALOG)

    def test_self_check_json(self):
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

    def _assert_refused(self, argv, code):
        status, payload = _run_json(argv)
        self.assertEqual(status, 2)
        self.assertEqual((payload["status"], payload["code"]), ("refused", code))

    def test_generate_refuses_existing_out(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "exists"
            out.mkdir()
            self._assert_refused(["generate", "--out", str(out), "--json"], "DESTINATION_EXISTS")

    def test_generate_refuses_raw_alias(self):
        raw = REPO / "outputs" / "raw" / "hopper-cli-should-refuse"
        self._assert_refused(["generate", "--out", str(raw), "--json"], "DESTINATION_UNDER_RAW")

    def test_wave_and_factory_selectors_filter_the_catalog(self):
        code, payload = _generate_fresh("--wave", "g46c", "--factory", "search-index-rebuild-factory")
        self.assertEqual(code, 0)
        self.assertGreater(payload["pairs"], 0)
        self.assertEqual({item["wave"] for item in payload["written"]}, {"g46c"})
        self.assertEqual({item["factory"] for item in payload["written"]},
                         {"search-index-rebuild-factory"})
        code, payload = _generate_fresh("--factory", "no-such-factory")
        self.assertEqual((code, payload["code"]), (2, "UNKNOWN_FACTORY"))
        code, payload = _generate_fresh("--wave", "g46c", "--slug", "no-such-slug")
        self.assertEqual((code, payload["code"]), (2, "UNKNOWN_SLUG"))

    def test_unknown_slug_refused(self):
        code, payload = _generate_fresh("--slug", "no-such-slug")
        self.assertEqual((code, payload["code"]), (2, "UNKNOWN_SLUG"))


if __name__ == "__main__":
    unittest.main()
