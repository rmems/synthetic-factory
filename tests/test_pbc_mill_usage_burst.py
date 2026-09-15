#!/usr/bin/env python3
"""First-slice PBC mill-usage-burst catalog (proto-breaking-change)."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402
from pbc import _contract  # noqa: E402
from pbc import catalog  # noqa: E402
from pbc import generate  # noqa: E402

_LEGACY = "origin/legacy-mill-lane"
_FIRST_SLUGS = {
    "pbc-mill-r701.py": "map-key-sfixed32-to-uint32",
    "pbc-mill-r731.py": "map-key-fixed64-to-uint64",
    "pbc-mill-r751.py": "int32-to-uint32-tap",
    "pbc-mill-r787.py": "int64-to-string-seq",
    "pbc-mill-r803.py": "http-copy-parent-path",
    "pbc-mill-r966.py": "timestamp-to-unix-seconds",
    "pbc-mill-r988.py": "int32-to-uint64-tap",
}


class PbcIdentityTests(unittest.TestCase):
    def test_reviewed_prefix_maps_to_factory(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[_contract.FAMILY], _contract.FACTORY)
        self.assertEqual(_contract.REVIEWED_HOME, _contract.FACTORY_NAME)
        self.assertEqual(_contract.SLICE_PAIR_COUNT, 8)
        self.assertEqual(_contract.FULL_PAIR_COUNT, 708)

    def test_refuse_vendor_paths_fails_closed(self):
        with self.assertRaises(SystemExit) as caught:
            _contract.refuse_vendor_paths((Path("experiments") / "pbc-mill-r701.py",))
        self.assertIn("pbc-mill-r701.py", str(caught.exception))


class PbcCatalogTests(unittest.TestCase):
    def test_plan_loads_first_slice_counts(self):
        plan = catalog.load_mill_usage_burst_plan(repo_root=REPO)
        self.assertEqual(plan.slice, "A")
        self.assertEqual(
            plan.counts(),
            {"mills": 8, "rounds": 8, "pairs": 8, "episodes": 16},
        )
        self.assertEqual(
            [mill.mill_id for mill in plan.mills],
            [
                "pbc_r701",
                "pbc_r731",
                "pbc_r751",
                "pbc_r787",
                "pbc_r803",
                "pbc_r966",
                "pbc_r988",
                "pbc_r2535",
            ],
        )
        self.assertNotIn(_contract.LEFTOVER_MILL_ID, [mill.mill_id for mill in plan.mills])

    def test_catalog_pins_first_pair_slugs(self):
        loaded = catalog.load_catalog()
        self.assertEqual(len(loaded.pairs), 8)
        first = loaded.mill("pbc_r701")
        self.assertEqual(first.ok["slug"], "map-key-sfixed32-to-uint32")
        self.assertEqual(first.bad["slug"], "float-to-double-temp")
        self.assertEqual(loaded.header["extract"]["leftover_first_slug"], "date-to-int32-poured")
        self.assertFalse(loaded.header["extract"]["exec"])

    def test_no_vendored_pbc_mill_scripts(self):
        hits = [
            str(path.relative_to(REPO))
            for path in REPO.rglob("pbc-mill*.py")
            if ".git" not in path.parts
        ]
        self.assertEqual(hits, [])
        loop_hits = [
            str(path.relative_to(REPO))
            for path in REPO.rglob("*-loop-*.py")
            if ".git" not in path.parts and "pbc" in path.name
        ]
        self.assertEqual(loop_hits, [])

    def test_record_builder_on_first_plant_pair(self):
        pair = catalog.load_catalog().mill("pbc_r701")
        rec_ok = generate.success_episode(pair.start, pair.ok)
        rec_bad = generate.handoff_episode(pair.start, pair.bad)
        self.assertEqual(rec_ok["id"], "pbc-r701-map-key-sfixed32-to-uint32-701a")
        self.assertEqual(rec_bad["id"], "pbc-r701-float-to-double-temp-701b")
        self.assertTrue(18 <= len(rec_ok["steps"]) <= 22)
        self.assertTrue(18 <= len(rec_bad["steps"]) <= 22)
        self.assertTrue(rec_ok["reward"]["success"])
        self.assertFalse(rec_bad["reward"]["success"])
        notes = generate.notes_for(
            pair.start,
            pair.ok,
            pair.bad,
            rec_ok,
            rec_bad,
            catalog_first=pair.catalog_first,
        )
        self.assertIn("Novel coverage:", notes)


class PbcAstExtractTests(unittest.TestCase):
    def test_plant_and_ty_and_raw_first_slugs_without_exec(self):
        plant_src = (
            "PAIRS = (plant(slug='map-key-sfixed32-to-uint32', short='s32k'), "
            "plant(slug='float-to-double-temp', short='f2d'))\n"
        )
        ty_src = "row = ty('int64-to-string-seq', 'i64s', 'int64')\n"
        raw_src = 'RAW = """\\nint32-to-uint64-tap|i32u64|int32\\n"""\n'
        self.assertEqual(generate.first_slugs_from_source(plant_src)[0], "map-key-sfixed32-to-uint32")
        self.assertEqual(generate.first_slugs_from_source(ty_src)[0], "int64-to-string-seq")
        self.assertEqual(generate.first_slugs_from_source(raw_src)[0], "int32-to-uint64-tap")

    def test_extract_tree_reads_temp_mill_text_only(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "pbc-mill-r701.py").write_text(
                "PAIRS = (plant(slug='map-key-sfixed32-to-uint32'),)\n",
                encoding="utf-8",
            )
            payload = generate.extract_tree(root)
        self.assertFalse(payload["extract"]["exec"])
        self.assertEqual(payload["rows"][0]["first_slug"], "map-key-sfixed32-to-uint32")

    def test_legacy_first_slugs_when_ref_available(self):
        probe = subprocess.run(
            ["git", "rev-parse", "--verify", _LEGACY],
            cwd=REPO,
            capture_output=True,
            text=True,
        )
        if probe.returncode != 0:
            fetched = subprocess.run(
                ["git", "fetch", "origin", "legacy-mill-lane"],
                cwd=REPO,
                capture_output=True,
                text=True,
            )
            if fetched.returncode != 0:
                self.skipTest("origin/legacy-mill-lane is not available")
        for script, slug in _FIRST_SLUGS.items():
            with self.subTest(script=script):
                text = subprocess.check_output(
                    ["git", "show", f"{_LEGACY}:experiments/{script}"],
                    text=True,
                    cwd=REPO,
                )
                self.assertEqual(generate.first_slugs_from_source(text)[0], slug)


if __name__ == "__main__":
    unittest.main()
