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


if __name__ == "__main__":
    unittest.main()
