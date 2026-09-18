#!/usr/bin/env python3
"""Fail-closed refusals for the cleaned db mill."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from pipelines.db.cli import main  # noqa: E402
from pipelines.db.episode import assert_clean, pair_for  # noqa: E402
from pipelines.db.notes import emit_stage  # noqa: E402
from pipelines.db.plant import make_plant  # noqa: E402
from pipelines.db.sql import engine_cmd  # noqa: E402


def _plant(**overrides):
    fields = {
        "engine": "sqlite",
        "slug": "sqlite-fixture-plant",
        "plant": "sqlite-fixture",
        "surface": "sqlite-fixture-surface",
        "table": "fixture_item",
        "col": "body",
        "col_v2": "body_v2",
        "leftover": "fixture_leftover",
        "leftover2": "fixture_leftover2",
        "seed": "ALTER TABLE fixture_item RENAME COLUMN body TO body_v2",
        "fail": "NOTICE: fixture fail",
        "inspect": "SELECT 1",
        "catalog": "fixture catalog",
        "abort": "SELECT 1",
        "col_type": "TEXT",
    }
    fields.update(overrides)
    return make_plant(**fields)


class CodedRefusals(unittest.TestCase):
    def test_unknown_engine_and_empty_fields_are_refused(self):
        with self.assertRaisesRegex(ValueError, "unknown engine 'postgres'"):
            _plant(engine="postgres")
        with self.assertRaisesRegex(ValueError, "empty slug"):
            _plant(slug="")

    def test_banned_payload_keys_are_refused(self):
        with self.assertRaisesRegex(ValueError, "banned key thought"):
            assert_clean({"thought": "nope"})
        with self.assertRaisesRegex(ValueError, "sim_or_real real"):
            assert_clean({"sim_or_real": "real"})
        with self.assertRaisesRegex(ValueError, "spike_events"):
            assert_clean({"spike_events": []})

    def test_pair_before_start_and_unknown_sql_engine_are_refused(self):
        with self.assertRaisesRegex(KeyError, "no plant pair for round 844"):
            pair_for(844)
        with self.assertRaisesRegex(ValueError, "unknown engine 'postgres'"):
            engine_cmd({"engine": "postgres", "db": "app.db"}, "SELECT 1")

    def test_staging_overwrite_and_unknown_cli_are_refused(self):
        with tempfile.TemporaryDirectory(prefix="dbm-refuse-") as td:
            dest = Path(td)
            emit_stage(dest, 845)
            with self.assertRaisesRegex(FileExistsError, "refuse to overwrite"):
                emit_stage(dest, 845)
        with self.assertRaisesRegex(SystemExit, r"usage: db.cli"):
            main(["--json"])


if __name__ == "__main__":
    unittest.main()
