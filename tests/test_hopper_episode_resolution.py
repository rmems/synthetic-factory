"""Hopper prefix and raw-root resolution: where each comes from, and the refusal when none does."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))
sys.path.insert(0, str(REPO / "tests"))

from hopper import build_pair, factory_dir
from hopper._contract import FINDING_PAIR_INVALID, FINDING_RAW_ROOT_REQUIRED
from hopper.episode import set_raw_root
from hopper.plants import _CATALOG
from hopper_test_support import G46C_SLUG, refusal

UNKNOWN_FACTORY = "not-a-hopper-factory"


def _unprefixed(plant):
    return {key: value for key, value in plant.items() if key != "prefix"}


class BuildPairPrefixTests(unittest.TestCase):
    def setUp(self):
        self.row = _CATALOG.pair_for_slug(G46C_SLUG)

    def test_known_factory_uses_its_registered_prefix(self):
        ok_ep, bad_ep, _ = build_pair(
            self.row.factory, self.row.published_round, self.row.ok, self.row.bad
        )
        self.assertEqual(ok_ep["id"], f"sir-r50-{G46C_SLUG}")
        self.assertTrue(bad_ep["id"].startswith("sir-r50-"))

    def test_unknown_factory_falls_back_to_a_plant_prefix(self):
        ok = dict(_unprefixed(self.row.ok), prefix="zz")
        bad = _unprefixed(self.row.bad)
        ok_ep, bad_ep, notes = build_pair(UNKNOWN_FACTORY, 7, ok, bad)
        self.assertTrue(ok_ep["id"].startswith("zz-r7-"))
        self.assertTrue(bad_ep["id"].startswith("zz-r7-"))
        self.assertIn(f"# {UNKNOWN_FACTORY} — NOTES r7", notes)

    def test_unknown_factory_without_any_prefix_is_refused(self):
        ok = _unprefixed(self.row.ok)
        bad = dict(_unprefixed(self.row.bad), prefix="")
        with refusal(self, FINDING_PAIR_INVALID, f"no prefix for factory {UNKNOWN_FACTORY}"):
            build_pair(UNKNOWN_FACTORY, 7, ok, bad)


class FactoryDirRootTests(unittest.TestCase):
    def tearDown(self):
        set_raw_root(None)

    def test_explicit_root_wins_over_the_module_root_and_environment(self):
        set_raw_root(Path("/srv/module-root"))
        with mock.patch.dict(os.environ, {"HOPPER_RAW_ROOT": "/srv/env-root"}):
            self.assertEqual(
                factory_dir("f", raw_root=Path("/srv/explicit")), Path("/srv/explicit/f")
            )
            self.assertEqual(factory_dir("f"), Path("/srv/module-root/f"))

    def test_environment_root_is_the_last_fallback(self):
        set_raw_root(None)
        with mock.patch.dict(os.environ, {"HOPPER_RAW_ROOT": "/srv/env-root"}):
            self.assertEqual(factory_dir("f"), Path("/srv/env-root/f"))
        with (
            mock.patch.dict(os.environ, {"HOPPER_RAW_ROOT": ""}),
            refusal(self, FINDING_RAW_ROOT_REQUIRED, "HOPPER_RAW_ROOT"),
        ):
            factory_dir("f")


if __name__ == "__main__":
    unittest.main()
