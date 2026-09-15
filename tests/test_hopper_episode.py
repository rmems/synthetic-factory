#!/usr/bin/env python3
"""Hopper episode shape, decision_basis contract, and one golden pair."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hopper_test_support import FIXTURE, G46C_SLUG, refusal  # noqa: E402

from hopper import (
    PAIRS,
    START,
    assert_clean,
    build_fail,
    build_success,
    dumps_episode,
    emit_stage,
    factory_dir,
    notes_md,
    validate_pair,
)
from hopper._contract import (
    FINDING_DESTINATION_EXISTS,
    FINDING_PAIR_INVALID,
    FINDING_PLANT_FIELD_MISSING,
    FINDING_RAW_ROOT_REQUIRED,
)
from hopper.episode import DB_PREFIXES, GENERATOR
from hopper.plants import _CATALOG


def _g46c_pair():
    return _CATALOG.pair_for_slug(G46C_SLUG)


class HopperEpisodeTests(unittest.TestCase):
    def test_success_and_fail_shapes(self):
        row = _g46c_pair()
        ok = build_success(row.factory, row.prefix, row.published_round, row.ok)
        bad = build_fail(row.factory, row.prefix, row.published_round, row.bad)
        validate_pair(ok, bad, row.published_round)
        self.assertEqual(len(ok["steps"]), 16)
        self.assertEqual(len(bad["steps"]), 17)
        self.assertTrue(ok["reward"]["success"])
        self.assertFalse(bad["reward"]["success"])
        self.assertEqual(ok["meta"]["generator"], GENERATOR)
        self.assertEqual(bad["meta"]["generator"], GENERATOR)
        self.assertEqual(ok["id"], f"sir-r50-{G46C_SLUG}")
        self.assertIn("502", ok["steps"][5]["observation"])
        self.assertIn("429", ok["steps"][7]["observation"])
        self.assertIn("429", bad["steps"][5]["observation"])
        self.assertIn("502", bad["steps"][7]["observation"])

    def test_decision_basis_prefix_and_width(self):
        row = _g46c_pair()
        ok = build_success(row.factory, row.prefix, row.published_round, row.ok)
        for step in ok["steps"]:
            self.assertTrue(step["decision_basis"].startswith(DB_PREFIXES))
            self.assertLessEqual(len(step["decision_basis"]), 240)

    def test_banned_keys_and_real_sim(self):
        with refusal(self, FINDING_PAIR_INVALID, "thought"):
            assert_clean({"thought": "nope"})
        with refusal(self, FINDING_PAIR_INVALID, "sim_or_real"):
            assert_clean({"sim_or_real": "real"})
        with refusal(self, FINDING_PAIR_INVALID, "spike_events"):
            assert_clean({"spike_events": []})

    def test_handoff_requires_ticket(self):
        row = _g46c_pair()
        bare = {key: row.bad[key] for key in row.bad if key != "ticket"}
        with refusal(self, FINDING_PLANT_FIELD_MISSING, "ticket"):
            build_fail(row.factory, row.prefix, row.published_round, bare)

    def test_notes_require_coverage(self):
        row = _g46c_pair()
        with refusal(self, "PLANT_FIELD_INVALID", "coverage"):
            notes_md(row.factory, row.published_round, {"domain": "x", "seed": "s", "plan_change": "p", "residual": "r"}, row.bad, "ok", "bad")

    def test_dumps_episode_is_compact(self):
        row = _g46c_pair()
        ok = build_success(row.factory, row.prefix, row.published_round, row.ok)
        text = dumps_episode(ok)
        self.assertEqual(text, json.dumps(ok, ensure_ascii=True, separators=(",", ":")))
        self.assertNotIn("\n", text)
        self.assertIn('{"id":', text)

    def test_emit_stage_and_fixture_replay(self):
        import tempfile
        from pathlib import Path
        row = _g46c_pair()
        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp) / "stage"
            ids = emit_stage(stage, row.factory, row.published_round, row.ok, row.bad)
            batch = (stage / f"batch-r{row.published_round:02d}.jsonl").read_text(encoding="utf-8")
            notes = (stage / f"NOTES-r{row.published_round:02d}.md").read_text(encoding="utf-8")
            expected_batch = (FIXTURE / "g46c-zombodb.batch.jsonl").read_text(encoding="utf-8")
            expected_notes = (FIXTURE / "g46c-zombodb.notes.md").read_text(encoding="utf-8")
            self.assertEqual(batch, expected_batch)
            self.assertEqual(notes, expected_notes)
            self.assertEqual(ids[0], f"sir-r50-{G46C_SLUG}")
            with refusal(self, FINDING_DESTINATION_EXISTS, "already exists"):
                emit_stage(stage, row.factory, row.published_round, row.ok, row.bad)

    def test_factory_dir_requires_root(self):
        import os
        from hopper.episode import set_raw_root
        set_raw_root(None)
        env = {key: value for key, value in os.environ.items() if key != "HOPPER_RAW_ROOT"}
        with mock.patch.dict(os.environ, env, clear=True):
            with refusal(self, FINDING_RAW_ROOT_REQUIRED, "HOPPER_RAW_ROOT"):
                factory_dir("rate-limit-backoff-factory")
        root = factory_dir("rate-limit-backoff-factory", raw_root="/tmp/hopper-raw")
        self.assertEqual(str(root), "/tmp/hopper-raw/rate-limit-backoff-factory")

    def test_public_start_pairs_drive_a_round(self):
        factory = "rate-limit-backoff-factory"
        ok, bad = PAIRS[factory][0]
        round_n = START[factory]
        built = build_success(factory, "rlb", round_n, ok)
        self.assertEqual(built["meta"]["round"], 53)
        self.assertTrue(bad["ticket"])


if __name__ == "__main__":
    unittest.main()
