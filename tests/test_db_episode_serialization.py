#!/usr/bin/env python3
"""Golden-byte coverage for the DB/DBM shared episode scaffold."""

from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from pipelines.db import config as db_config  # noqa: E402
from pipelines.db.episode import build_episode as build_db_episode  # noqa: E402
from pipelines.db.episode import dumps_episode as dumps_db_episode  # noqa: E402
from pipelines.db.plants import PLANTS  # noqa: E402
from pipelines.db_episode_scaffold import (  # noqa: E402
    EpisodeAssembly,
    assemble_episode,
    bash,
    step,
    write,
)
from pipelines.dbm.catalog import catalog_check  # noqa: E402
from pipelines.dbm import episode as dbm_episode  # noqa: E402
from pipelines.dbm._contract import (  # noqa: E402
    DbmRefusal,
    FINDING_GENERATE_GOAL,
    FINDING_GENERATE_HIDDEN,
)


class EpisodeSerializationCompatibility(unittest.TestCase):
    def test_each_db_engine_matches_its_pre_refactor_bytes(self):
        expected = {
            "mysql": "99d568d5f374097bbe1589ead281f97813f96fa4aa13a29d6f8ecb4c95224e17",
            "sqlite": "566554f5b22b614ee6a86f1a99c34901742f75373b12c36987201c4dc1d179d1",
            "mssql": "e067bf9ec7f25308a8f323617457b327fcbac31b0c4bc0d33d7113eef1421db4",
            "oracle": "525b97fcbec3228b4caa6393ffa5e3d055e67a32ff4c7de4a1833518bb54598b",
            "mariadb": "499f0d571d51295a38349a2eaea628382835f7afd42a57361eb25ef2ac994ddc",
            "crdb": "8ee1b75eeaaf40dbe6a25c5477956a4667a3b6b3c72139c27c4ced28132d8e47",
        }
        representatives = {}
        for plant in PLANTS:
            representatives.setdefault(plant["engine"], plant)
        for engine, digest in expected.items():
            with self.subTest(engine=engine):
                episode = build_db_episode(db_config.START_ROUND, representatives[engine], 0)
                serialized = dumps_db_episode(episode).encode("utf-8")
                self.assertEqual(hashlib.sha256(serialized).hexdigest(), digest)

    def test_dbm_preserved_lane_matches_its_pre_refactor_bytes(self):
        catalog = catalog_check(root=REPO).leftover3
        episode = dbm_episode.build_episode(catalog.start_round, catalog.plants[0], 0)
        serialized = dbm_episode.dumps_episode(episode).encode("utf-8")
        self.assertEqual(
            hashlib.sha256(serialized).hexdigest(),
            "354a2280bd381f365e148d51203f738a510f29f0b77371dd72925a02873237f5",
        )

    def test_dbm_refusal_adapters_remain_lane_specific(self):
        catalog = catalog_check(root=REPO).leftover3
        with self.assertRaises(DbmRefusal) as hidden:
            dbm_episode._assert_clean({"thought": "nope"})
        self.assertEqual(hidden.exception.code, FINDING_GENERATE_HIDDEN)

        malformed = dict(catalog.plants[0])
        malformed["plant"] = "fixture [Variant 2]"
        with self.assertRaises(DbmRefusal) as variant:
            dbm_episode.build_episode(catalog.start_round, malformed, 0)
        self.assertEqual(variant.exception.code, FINDING_GENERATE_GOAL)


class ScaffoldPrimitives(unittest.TestCase):
    def test_bash_write_step_and_assemble_episode_shapes(self):
        tool = bash("echo ok")
        self.assertEqual(tool, {"name": "bash", "args": {"command": "echo ok"}})
        written = write("docs/a.md", "body")
        self.assertEqual(
            written,
            {"name": "write", "args": {"path": "docs/a.md", "contents": "body"}},
        )
        one = step(1, "basis", tool, "obs")
        self.assertEqual(
            one,
            {"n": 1, "decision_basis": "basis", "tool_call": tool, "observation": "obs"},
        )
        episode = assemble_episode(
            EpisodeAssembly(
                episode_id="dbm-r845-fixture",
                goal="goal",
                plan="plan",
                steps=[one],
                outcome="outcome",
                meta={"factory": "db-migration-repair-factory", "kind": "episode"},
            )
        )
        self.assertEqual(episode["id"], "dbm-r845-fixture")
        self.assertEqual(episode["steps"], [one])
        self.assertEqual(
            episode["reward"],
            {
                "success": True,
                "apply_fails": 2,
                "plan_changes": 1,
                "lock_timeouts": 1,
                "tests_passed": 4,
                "cost_steps": 1,
            },
        )
        self.assertEqual(episode["meta"]["kind"], "episode")


class FlatImportPaths(unittest.TestCase):
    def test_db_and_dbm_episode_flat_imports_resolve_scaffold(self):
        """Exercise the non-pipelines import branch on both episode modules."""
        import sys

        pipelines_dir = str(REPO / "pipelines")
        if pipelines_dir not in sys.path:
            sys.path.insert(0, pipelines_dir)
        for key in (
            "db.episode",
            "pipelines.db.episode",
            "dbm.episode",
            "pipelines.dbm.episode",
        ):
            sys.modules.pop(key, None)

        import db.episode as db_flat  # noqa: E402
        import dbm.episode as dbm_flat  # noqa: E402

        self.assertEqual(db_flat.__name__, "db.episode")
        self.assertEqual(dbm_flat.__name__, "dbm.episode")
        self.assertEqual(
            db_flat._bash("true"),
            {"name": "bash", "args": {"command": "true"}},
        )
        self.assertEqual(
            dbm_flat._write("x.sql", "--"),
            {"name": "write", "args": {"path": "x.sql", "contents": "--"}},
        )
        db_flat.assert_clean({"meta": {"sim_or_real": "designed"}})


if __name__ == "__main__":
    unittest.main()
