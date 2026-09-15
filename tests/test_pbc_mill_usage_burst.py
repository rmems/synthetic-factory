#!/usr/bin/env python3
"""Mill-usage-burst plan slice A (``pbc`` / proto-breaking-change)."""

from __future__ import annotations

import ast
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import pbc.plants_r1335 as plants_r1335  # noqa: E402
import pbc.plants_r2535 as plants_r2535  # noqa: E402
import pbc.plants_r701 as plants_r701  # noqa: E402
import pbc.plants_r731 as plants_r731  # noqa: E402
import pbc.plants_r751 as plants_r751  # noqa: E402
import pbc.plants_r787 as plants_r787  # noqa: E402
import pbc.plants_r803 as plants_r803  # noqa: E402
import pbc.plants_r966 as plants_r966  # noqa: E402
import pbc.plants_r988 as plants_r988  # noqa: E402
import pbc.record_builder as pbc_builder  # noqa: E402
from pbc.usage_burst_plan import load_mill_usage_burst_plan  # noqa: E402
from pbc import vocabulary as pv  # noqa: E402
from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402

_LEGACY = "origin/legacy-mill-lane"
_STATIC_MILLS = (
    ("pbc-mill-r701.py", plants_r701),
    ("pbc-mill-r731.py", plants_r731),
    ("pbc-mill-r751.py", plants_r751),
    ("pbc-mill-r787.py", plants_r787),
    ("pbc-mill-r803.py", plants_r803),
    ("pbc-mill-r966.py", plants_r966),
)


def _git_show(path: str) -> str:
    return subprocess.check_output(
        ["git", "show", f"{_LEGACY}:experiments/{path}"],
        text=True,
        cwd=REPO,
    )


def _ensure_legacy_ref() -> bool:
    probe = subprocess.run(
        ["git", "rev-parse", "--verify", _LEGACY],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    if probe.returncode == 0:
        return True
    fetched = subprocess.run(
        ["git", "fetch", "origin", "legacy-mill-lane"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    return fetched.returncode == 0


def _exec_named(tree: ast.Module, names: set[str], ns: dict) -> None:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            exec(ast.unparse(node), ns)
            continue
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in names:
                    exec(ast.unparse(node), ns)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id in names and node.value is not None:
                exec(ast.unparse(node), ns)


def _legacy_pairs(script_name: str) -> tuple[list, int]:
    mill = ast.parse(_git_show(script_name))
    ns: dict = {}
    if script_name == "pbc-mill-r787.py":
        r701 = ast.parse(_git_show("pbc-mill-r701.py"))
        _exec_named(r701, {"plant"}, ns)
        _exec_named(
            mill,
            {
                "ty",
                "ENUM_GRADE",
                "ENUM_MODE",
                "ENUM_STATE",
                "MSG_NOTE",
                "MSG_BLOB",
                "MSG_EVT",
                "PAIRS",
                "CATALOG_FIRST",
            },
            ns,
        )
    else:
        r701 = ast.parse(_git_show("pbc-mill-r701.py"))
        _exec_named(r701, {"plant"}, ns)
        _exec_named(mill, {"PAIRS", "CATALOG_FIRST"}, ns)
    return ns["PAIRS"], ns["CATALOG_FIRST"]


def _legacy_r988_pairs() -> list:
    r701 = ast.parse(_git_show("pbc-mill-r701.py"))
    r787 = ast.parse(_git_show("pbc-mill-r787.py"))
    r988 = ast.parse(_git_show("pbc-mill-r988.py"))
    ns: dict = {}
    _exec_named(r701, {"plant"}, ns)
    _exec_named(r787, {"ty", "ENUM_MODE"}, ns)
    _exec_named(r988, {"RAW", "LANGC", "_extras_for", "_parse_rows"}, ns)
    plants = ns["_parse_rows"]()
    return [(plants[i], plants[i + 1]) for i in range(0, len(plants), 2)]


def _legacy_r2535_pairs() -> list:
    r701 = ast.parse(_git_show("pbc-mill-r701.py"))
    r787 = ast.parse(_git_show("pbc-mill-r787.py"))
    r2535 = ast.parse(_git_show("pbc-mill-r2535.py"))
    ns: dict = {}
    _exec_named(r701, {"plant"}, ns)
    _exec_named(r787, {"ty", "ENUM_MODE"}, ns)
    _exec_named(
        r2535,
        {
            "LANGC",
            "WKT_DESTS",
            "P2_TYPES",
            "BANNED_SLUGS",
            "BANNED_NEEDLES",
            "_guard",
            "_extras_for",
            "_mk",
            "_build_plants",
        },
        ns,
    )
    ns["LANGS"] = list(ns["LANGC"])
    plants = ns["_build_plants"]()
    return [(plants[i], plants[i + 1]) for i in range(0, len(plants), 2)]


class PbcMillUsageBurstTests(unittest.TestCase):
    def test_reviewed_prefix_maps_to_factory(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[pv.FAMILY_PREFIX], pv.FACTORY)

    def test_plan_loads_and_matches_plants(self):
        plan = load_mill_usage_burst_plan(repo_root=REPO)
        self.assertEqual(plan.slice, "A")
        self.assertEqual(
            plan.counts(),
            {"mills": 8, "rounds": 708, "pairs": 708, "episodes": 1416},
        )
        self.assertEqual(
            [m.mill_id for m in plan.mills],
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

    def test_no_vendored_pbc_mill_scripts(self):
        hits = [
            str(path.relative_to(REPO))
            for path in REPO.rglob("pbc-mill*.py")
            if ".git" not in path.parts
        ]
        self.assertEqual(hits, [])

    def test_record_builder_on_first_plant_pair(self):
        ok, bad = plants_r701.PAIRS[0]
        rnd = plants_r701.START
        rec_ok = pbc_builder.success_episode(rnd, ok)
        rec_bad = pbc_builder.handoff_episode(rnd, bad)
        self.assertEqual(rec_ok["id"], "pbc-r701-map-key-sfixed32-to-uint32-701a")
        self.assertEqual(rec_bad["id"], "pbc-r701-float-to-double-temp-701b")
        self.assertTrue(18 <= len(rec_ok["steps"]) <= 22)
        self.assertTrue(18 <= len(rec_bad["steps"]) <= 22)
        self.assertTrue(rec_ok["reward"]["success"])
        self.assertFalse(rec_bad["reward"]["success"])
        self.assertEqual(rec_ok["meta"]["factory"], pv.FACTORY)
        self.assertEqual(rec_ok["meta"]["generator"], pv.GENERATOR)
        notes = pbc_builder.notes_for(
            rnd,
            ok,
            bad,
            rec_ok,
            rec_bad,
            catalog_first=plants_r701.CATALOG_FIRST,
        )
        self.assertIn("Novel coverage:", notes)

    def test_episode_ids_are_deterministic(self):
        ok, _bad = plants_r701.PAIRS[0]
        self.assertEqual(
            pbc_builder.success_episode(701, ok)["id"],
            pbc_builder.success_episode(701, ok)["id"],
        )


class PbcLegacyAstExtractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not _ensure_legacy_ref():
            raise unittest.SkipTest("origin/legacy-mill-lane is not available")

    def test_static_plants_match_legacy_ast_extract(self):
        for script, module in _STATIC_MILLS:
            with self.subTest(script=script):
                legacy_pairs, catalog_first = _legacy_pairs(script)
                self.assertEqual(catalog_first, module.CATALOG_FIRST)
                self.assertEqual(len(legacy_pairs), len(module.PAIRS))
                self.assertEqual(legacy_pairs[0][0]["slug"], module.PAIRS[0][0]["slug"])
                self.assertEqual(
                    [pair[0]["slug"] for pair in legacy_pairs],
                    [pair[0]["slug"] for pair in module.PAIRS],
                )

    def test_r988_matches_legacy_raw_parse(self):
        legacy_pairs = _legacy_r988_pairs()
        self.assertEqual(len(legacy_pairs), len(plants_r988.PAIRS))
        self.assertEqual(legacy_pairs[0][0]["slug"], plants_r988.PAIRS[0][0]["slug"])
        self.assertEqual(legacy_pairs[0][0]["slug"], "int32-to-uint64-tap")

    def test_r2535_matches_legacy_build(self):
        legacy_pairs = _legacy_r2535_pairs()
        self.assertEqual(len(legacy_pairs), len(plants_r2535.PAIRS))
        self.assertEqual(legacy_pairs[0][0]["slug"], plants_r2535.PAIRS[0][0]["slug"])
        self.assertEqual(
            legacy_pairs[0][0]["slug"],
            "proto2-required-int32-to-timestamp",
        )

    def test_r1335_leftover_first_slug_with_empty_taken(self):
        r701 = ast.parse(_git_show("pbc-mill-r701.py"))
        r787 = ast.parse(_git_show("pbc-mill-r787.py"))
        r1335 = ast.parse(_git_show("pbc-mill-r1335.py"))
        ns: dict = {"used_slugs": lambda: set()}
        _exec_named(r701, {"plant"}, ns)
        _exec_named(r787, {"ty", "ENUM_MODE"}, ns)
        _exec_named(
            r1335,
            {
                "LANGC",
                "DESTS",
                "DEST_TAGS",
                "SOURCES",
                "MAP_VALS",
                "P2_TYPES",
                "BANNED_SLUGS",
                "BANNED_NEEDLES",
                "_dest_of",
                "_taken_index",
                "_pair_taken",
                "_guard",
                "_extras_for",
                "_mk",
                "_build_plants",
            },
            ns,
        )
        ns["LANGS"] = list(ns["LANGC"])
        legacy = ns["_build_plants"]()
        cleaned = plants_r1335.build_plants(taken_slugs=())
        self.assertEqual(legacy[0]["slug"], cleaned[0]["slug"])
        self.assertEqual(legacy[0]["slug"], "date-to-int32-poured")
        self.assertEqual(len(legacy), len(cleaned))
        plan = load_mill_usage_burst_plan(repo_root=REPO)
        self.assertNotIn("pbc_r1335", [m.mill_id for m in plan.mills])


if __name__ == "__main__":
    unittest.main()
