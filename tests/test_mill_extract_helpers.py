"""Branch coverage for the private extraction helpers in search, tup, db.sql and dlk.cli.

Every source here is a small synthetic literal, so these tests run without the
legacy mill refs being fetched. They pin the refusal messages and the order of
checks the refactored helpers must keep.
"""

from __future__ import annotations

import ast
import contextlib
import importlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

search_extract = importlib.import_module("search.catalog_extract")
tup_extract = importlib.import_module("tup.catalog_extract")
TupRefusal = importlib.import_module("tup._contract").TupRefusal
db_sql = importlib.import_module("db.sql")
dlk_cli = importlib.import_module("dlk.cli")
dlk_contract = importlib.import_module("dlk._contract")

ARM_A = "('a', 'b', 'c', 'd', 'e', 'f')"
ARM_B = "('g', 'h', 'i', 'j', 'k', 'l')"
ONE_PAIR = f"PAIRS = [({ARM_A}, {ARM_B})]\n"
HOME_PATH = "experiments/sir-mill-r99.py"
MILL_PATH = "experiments/search_mill_probe.py"


class SearchHomeExtractTests(unittest.TestCase):
    def extract(self, source: str) -> dict:
        return search_extract.extract_home_mill_catalog(source, path=HOME_PATH, blob_sha="b")

    def test_home_record_numbers_rounds_and_carries_slice(self) -> None:
        record = self.extract(
            '"""\n\n  Home doc.\n"""\nCATALOG_FIRST = 5\nN_ROUNDS = 1\n' + ONE_PAIR
        )
        self.assertEqual(record["slice"], "sir-mill-r99")
        self.assertEqual(record["n_rounds"], 1)
        self.assertEqual(record["n_hops"], 0)
        self.assertEqual(record["hops"], [])
        self.assertEqual(record["doc_first_line"], "Home doc.")
        self.assertEqual(record["pairs"][0]["round"], 5)
        self.assertEqual(record["pairs"][0]["mill_id"], "sir-mill-r99")

    def test_home_refuses_hops(self) -> None:
        with self.assertRaisesRegex(ValueError, "has HOP destinations"):
            self.extract("HOP = ['a-factory']\n")

    def test_home_refuses_blank_factory_and_bad_generator(self) -> None:
        with self.assertRaisesRegex(ValueError, "FACTORY is not a non-empty string"):
            self.extract("FACTORY = ''\n")
        with self.assertRaisesRegex(ValueError, "GEN is not a non-empty string"):
            self.extract("GEN = 3\n")

    def test_home_refuses_bool_catalog_first(self) -> None:
        with self.assertRaisesRegex(ValueError, "CATALOG_FIRST is not an int"):
            self.extract("CATALOG_FIRST = True\n" + ONE_PAIR)

    def test_home_refuses_n_rounds_that_disagree(self) -> None:
        with self.assertRaisesRegex(ValueError, "N_ROUNDS=3 disagrees with 1 pairs"):
            self.extract("CATALOG_FIRST = 5\nN_ROUNDS = 3\n" + ONE_PAIR)

    def test_home_refuses_leftover_pair_slug(self) -> None:
        source = (
            f"CATALOG_FIRST = 5\nPAIRS = [(('x-leftover3', 'b', 'c', 'd', 'e', 'f'), {ARM_B})]\n"
        )
        with self.assertRaisesRegex(ValueError, r"PAIRS\[0\]\.success_slug is leftover3/lll"):
            self.extract(source)


class SearchLeftoverExtractTests(unittest.TestCase):
    def extract(self, source: str) -> dict:
        return search_extract.extract_mill_catalog(source, path=MILL_PATH, blob_sha="b")

    def test_leftover_record_keeps_hops(self) -> None:
        record = self.extract(
            "FACTORY = 'f'\nGEN = 'g'\nCATALOG_FIRST = 5\nN_ROUNDS = 1\n"
            "HOP = ['a-factory', 'b-factory']\n" + ONE_PAIR
        )
        self.assertEqual(record["hops"], ["a-factory", "b-factory"])
        self.assertEqual(record["n_hops"], 2)
        self.assertEqual((record["factory"], record["generator"]), ("f", "g"))
        self.assertNotIn("slice", record)

    def test_leftover_refusals_in_check_order(self) -> None:
        cases = (
            ("GEN = ''\nCATALOG_FIRST = 'x'\n", "GEN is not a non-empty string"),
            ("CATALOG_FIRST = 'x'\nN_ROUNDS = 0\n", "CATALOG_FIRST is not an int"),
            ("CATALOG_FIRST = 1\nN_ROUNDS = 0\n", "N_ROUNDS is not a positive int"),
            ("CATALOG_FIRST = 1\nN_ROUNDS = 1\nHOP = ['x']\n", "HOP is not a literal list"),
            (
                "CATALOG_FIRST = 1\nN_ROUNDS = 2\nHOP = ['a-factory']\n" + ONE_PAIR,
                "N_ROUNDS=2 disagrees with 1 pairs",
            ),
        )
        for source, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                self.extract(source)


class SearchHomeRowsTests(unittest.TestCase):
    def load(self, body: str) -> list:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rows.jsonl"
            path.write_text(body, encoding="utf-8")
            return search_extract.load_home_rows("sir-mill-r72", path)

    def test_rows_load_in_order(self) -> None:
        rows = self.load('{"mill_id":"sir-mill-r72","n":1}\n{"mill_id":"sir-mill-r72","n":2}\n')
        self.assertEqual([row["n"] for row in rows], [1, 2])

    def test_row_refusals_name_the_line(self) -> None:
        cases = (
            ('{"mill_id":"sir-mill-r72"}\n\n', "line 2 is empty"),
            ("[1]\n", "line 1 is not an object"),
            (
                '{"mill_id":"sir-mill-r72","success_slug":"a-leftover3"}\n',
                "line 1 is leftover3/lll",
            ),
            (
                '{"mill_id":"sir-mill-r72","fail_slug":"a-leftover-lll"}\n',
                "line 1 is leftover3/lll",
            ),
            ('{"mill_id":"other"}\n', "line 1 mill_id is not sir-mill-r72"),
        )
        for body, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                self.load(body)


class TupAssignmentLookupTests(unittest.TestCase):
    def test_annotated_specs_are_found_and_later_rows_rebinding_is_skipped(self) -> None:
        source = "ROWS: list = [('l', 's', 't x', 'g', 'b', 'src', 'v', 'grep')]\nROWS = 3\n"
        rows = tup_extract.plant_rows_from_source(source, mill_id="m", var="ROWS")
        self.assertEqual([row["slug"] for row in rows], ["s"])
        self.assertEqual(rows[0]["bin"], "t")

    def test_multi_target_assign_is_not_a_row_list(self) -> None:
        with self.assertRaisesRegex(TupRefusal, "missing"):
            tup_extract.plant_rows_from_source("ROWS = SPECS = [('a',)]\n", mill_id="m")

    def test_plants_found_through_annotation_or_any_assign_target(self) -> None:
        call = "plant('l','s','t','g','b','k','r',3,'s','v','gr','vc','dc')"
        for source in (f"PLANTS: list = [{call}]\n", f"x = PLANTS = [{call}]\n"):
            with self.subTest(source=source):
                rows = tup_extract.leftover_plants_from_source(source, mill_id="m")
                self.assertEqual(rows[0]["verify"], "vc")
        with self.assertRaisesRegex(TupRefusal, "missing PLANTS"):
            tup_extract.leftover_plants_from_source("PLANTS: list\n", mill_id="m")

    def test_last_rounds_assignment_wins_and_annotations_are_ignored(self) -> None:
        source = (
            "ROUNDS = [[('s1', 't', 'f', 'v', 'd', 'k', 'g', 3)]]\n"
            "ROUNDS: list = [[('s9', 't', 'f', 'v', 'd', 'k', 'g', 9)]]\n"
            "ROUNDS = [[('s2', '', 'f', 'v', 'd', 'k', 'g', 4)],\n"
            "          [('s3', 't u', 'f', 'v', 'd', 'k', 'g', 5)]]\n"
        )
        rows = tup_extract.round_plants_from_source(source, mill_id="m")
        self.assertEqual(
            [(row["slug"], row["bin"], row["wait"]) for row in rows],
            [("s2", "", 4), ("s3", "t", 5)],
        )

    def test_round_plant_refusals(self) -> None:
        cases = (
            ("ROUNDS = [('s',)]\n", r"ROUNDS\[0\] is not a list"),
            ("ROUNDS = [[('s', 't')]]\n", r"ROUNDS\[0\]\[0\] is not an 8-tuple"),
            (
                "ROUNDS = [[('s','t','f','v','d','k','g',x)]]\n",
                r"ROUNDS\[0\]\[0\]\.wait is not a literal",
            ),
            ("ROUNDS = [[]]\n", "ROUNDS is empty"),
            ("ROUNDS: list = []\n", "missing ROUNDS"),
        )
        for source, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(TupRefusal, message):
                tup_extract.round_plants_from_source(source, mill_id="m")


class TupFamilyTests(unittest.TestCase):
    def test_widest_family_function_is_chosen(self) -> None:
        source = (
            "def extra_v1():\n    families = 3\n"
            "def extra_catalog():\n    families = [('b','k','g',[('s','v','d')])]\n"
            "def extra_v3():\n"
            "    families = [('b','k','g',[('s','v','d')]), ('c','k','g',[('t','v','rm d')])]\n"
        )
        rows = tup_extract.family_rows_from_source(source)
        self.assertEqual([row["bin"] for row in rows], ["b", "c"])
        self.assertEqual(rows[1]["cmds"], [["t", "v", "rm d"]])

    def test_first_families_binding_must_be_a_list(self) -> None:
        source = (
            "def extra_v2():\n    families = 3\n    families = [('b','k','g',[('s','v','d')])]\n"
        )
        with self.assertRaisesRegex(TupRefusal, "missing families list"):
            tup_extract.family_rows_from_source(source)

    def test_family_refusals(self) -> None:
        cases = (
            ("def extra():\n    families = [('b','k','g')]\n", r"families\[0\] is not a 4-tuple"),
            ("def extra():\n    families = [('b','k','g',[])]\n", r"families\[0\]\.cmds is empty"),
            (
                "def extra():\n    families = [('b','k','g',[('s','v')])]\n",
                r"families\[0\]\.cmds\[0\] is not a 3-tuple",
            ),
            (
                "def extra():\n    families = [('b','k','',[('s','v','d')])]\n",
                r"families\[0\]\.grep",
            ),
            ("def extra():\n    families = []\n", "families is empty"),
            ("def other():\n    families = []\n", "missing extra_"),
            ("def (:\n", "not parseable"),
        )
        for source, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(TupRefusal, message):
                tup_extract.family_rows_from_source(source)

    def test_expansion_skips_banned_and_reserved_slugs(self) -> None:
        rows = [
            {
                "bin": "yq",
                "keep": "k",
                "grep": "g",
                "cmds": [
                    ["eval-x", "v", "d"],
                    ["ok", " ", "rm x"],
                    ["b", "v", "yq z"],
                    ["q1", "v", "d"],
                    ["d2", "v", "drop"],
                ],
            },
            {"bin": "pacman", "keep": "k", "grep": "g", "cmds": [["x", "v", "d"]]},
        ]
        plants = tup_extract.expand_family_rows(
            rows, mill_id="m", banned_slugs=["yq-b"], banned_prefix=["yq-q"]
        )
        self.assertEqual(
            [(p["slug"], p["verify"], p["destroy"], p["wait"]) for p in plants],
            [("yq-ok", "yq", "rm x", 3), ("yq-d2", "yq v", "yq drop", 4)],
        )


DB_PLANT = {
    "engine": "sqlite",
    "table": "t",
    "col_v2": "c2",
    "col_type": "INT",
    "seed": "UPDATE t",
    "db": "x.db",
}


class DbSqlTemplateTests(unittest.TestCase):
    def test_templates_substitute_without_touching_braces_in_sql(self) -> None:
        self.assertEqual(
            db_sql.engine_cmd(DB_PLANT, "SELECT '{a}'"), "sqlite3 x.db \"SELECT '{a}'\""
        )
        self.assertEqual(
            db_sql.lock_sql(dict(DB_PLANT, engine="crdb")),
            "SET lock_timeout = '8s'; ALTER TABLE t ADD COLUMN IF NOT EXISTS c2 INT",
        )
        self.assertEqual(db_sql.seed_cmd_for(dict(DB_PLANT, seed="gh-ost --x")), "gh-ost --x")

    def test_unknown_engine_refused_by_every_builder(self) -> None:
        plant = dict(DB_PLANT, engine="pg")
        for build in (
            db_sql.expand_sql,
            db_sql.lock_sql,
            db_sql.default_lock_fail,
            db_sql.seed_cmd_for,
        ):
            with (
                self.subTest(build=build.__name__),
                self.assertRaisesRegex(ValueError, "unknown engine 'pg'"),
            ):
                build(plant)


class DlkExecSurfaceTests(unittest.TestCase):
    def names(self, source: str) -> list:
        found = []
        for node in ast.walk(ast.parse(source)):
            found.extend(dlk_cli._banned_names(node))
        return found

    def test_banned_imports_and_defs_carry_their_line(self) -> None:
        source = (
            "import os, subprocess.x\nfrom subprocess import run\nfrom . import ok\n"
            "from os import path\ndef main():\n    pass\n"
            "async def txn():\n    pass\ndef fine():\n    pass\n"
        )
        self.assertEqual(
            sorted(self.names(source)),
            [
                ("banned_def", "main", 5),
                ("banned_def", "txn", 7),
                ("banned_import", "subprocess", 2),
                ("banned_import", "subprocess.x", 1),
            ],
        )

    def test_round_findings_and_audit_report(self) -> None:
        bad = SimpleNamespace(round=1, factory="other", generator="gen-x", slugs=("a", "a"))
        good = SimpleNamespace(
            round=2, factory=dlk_contract.FACTORY, generator=dlk_contract.GEN, slugs=("a",)
        )
        self.assertEqual(
            [f["code"] for f in dlk_cli._round_findings(bad)],
            ["factory_mismatch", "generator_mismatch", "duplicate_slug"],
        )
        self.assertEqual(dlk_cli._round_findings(good), [])
        args = SimpleNamespace(config_dir=None)
        with (
            mock.patch.object(dlk_cli.cat, "load_all", return_value=[bad, good]),
            mock.patch.object(
                dlk_cli.cat, "catalog_index", return_value={"preserved_rounds": [1, 2, 3]}
            ),
            mock.patch.object(dlk_cli, "_scan_exec_surface", return_value=[]),
            contextlib.redirect_stdout(io.StringIO()) as out,
        ):
            self.assertEqual(dlk_cli._audit(args), 1)
        report = out.getvalue()
        for code in ("factory_mismatch", "cross_round_slug_overlap", "round_count"):
            self.assertIn(code, report)

    def test_audit_refuses_an_unloadable_catalog(self) -> None:
        args = SimpleNamespace(config_dir=None)
        with (
            mock.patch.object(dlk_cli.cat, "load_all", side_effect=KeyError("r9")),
            contextlib.redirect_stdout(io.StringIO()) as out,
        ):
            self.assertEqual(dlk_cli._audit(args), 2)
        self.assertIn('"status": "refused"', out.getvalue())


if __name__ == "__main__":
    unittest.main()
