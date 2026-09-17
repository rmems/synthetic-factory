#!/usr/bin/env python3
"""The cleaned ``brw`` family home under ``pipelines/brw/``.

``brw-mill-r193`` was AST-extracted from ``origin/legacy-mill-lane``. These
tests pin identity, catalog fidelity, and episode shape without publishing a
raw round, without importing a ``*mill*.py`` module, and without executing
leftover mill source.
"""

from __future__ import annotations

import ast
import contextlib
import io
import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BRW_DIR = REPO / "pipelines" / "brw"
sys.path.insert(0, str(REPO / "pipelines"))

from mill_family import REVIEWED_MILL_PREFIX_HOMES, mill_prefix  # noqa: E402
from brw import catalog  # noqa: E402
from brw import generate  # noqa: E402
from brw._contract import (  # noqa: E402
    BANNED,
    BANNED_CSS,
    BANNED_HOSTS,
    CATALOG_FIRST,
    FACTORY,
    FAMILY_PREFIX,
    GEN,
    MAX_STEPS,
    MIN_STEPS,
    SOURCE_MILL_ID,
    SOURCE_PATH,
    SOURCE_ROUND,
    BrwError,
)
from brw.cli import run as brw_run  # noqa: E402

EXPECTED_OK_SLUGS = (
    "branleat-offset-anchor",
    "dunlinbar-mask-image",
    "fenberry-filter-url",
    "harebell-display-contents",
    "jessamine-subgrid",
    "lampwick-dvh",
    "nakerbar-target-text",
    "partridge-backdrop-filter",
    "sallowfen-box-decoration-break",
    "umberquay-auto-phrase",
    "woldmere-overflow-clip-margin",
    "yarefen-will-change",
    "brimstone-backface",
    "dockleaf-dense",
    "fritillary-keyboard-inset",
    "hornbeam-nth-of",
)
SHIFT_SUCCESS_TOOLS = (
    "browser_navigate",
    "browser_snapshot",
    "browser_evaluate",
    "http_request",
    "browser_click",
    "browser_click",
    "browser_screenshot",
    "browser_evaluate",
    "browser_click",
    "browser_fill_form",
    "browser_click",
    "http_request",
    "browser_snapshot",
    "write",
)
FAIL_TOOLS = (
    "browser_navigate",
    "browser_snapshot",
    "http_request",
    "browser_evaluate",
    "browser_fill_form",
    "browser_screenshot",
    "http_request",
    "http_request",
    "http_request",
    "browser_snapshot",
    "browser_click",
    "browser_wait",
    "write",
)
PACKAGE_FILES = (
    "__init__.py",
    "_contract.py",
    "catalog.py",
    "cli.py",
    "generate.py",
)
LEGACY_ASSIGN_NAMES = frozenset(
    {"FACTORY", "GEN", "CATALOG_FIRST", "BANNED_HOSTS", "BANNED_CSS"}
)


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = brw_run(argv)
    return code, out.getvalue(), err.getvalue()


def _legacy_literals():
    src = subprocess.check_output(
        ["git", "show", f"origin/legacy-mill-lane:{SOURCE_PATH}"],
        text=True,
        cwd=REPO,
        stderr=subprocess.DEVNULL,
    )
    tree = ast.parse(src)
    ns = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names = [
                target.id
                for target in node.targets
                if isinstance(target, ast.Name) and target.id in LEGACY_ASSIGN_NAMES
            ]
            if names:
                value = ast.literal_eval(node.value)
                for name in names:
                    ns[name] = value
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "PAIRS"
        ):
            ns["PAIRS"] = ast.literal_eval(node.value)
    return ns


def _legacy_function_names():
    src = subprocess.check_output(
        ["git", "show", f"origin/legacy-mill-lane:{SOURCE_PATH}"],
        text=True,
        cwd=REPO,
        stderr=subprocess.DEVNULL,
    )
    tree = ast.parse(src)
    return tuple(
        node.name for node in tree.body if isinstance(node, ast.FunctionDef)
    )


class BrwPackageLayout(unittest.TestCase):
    def test_family_home_is_the_five_cleaned_modules(self):
        names = tuple(sorted(path.name for path in BRW_DIR.iterdir() if path.suffix == ".py"))
        self.assertEqual(names, tuple(sorted(PACKAGE_FILES)))
        self.assertFalse(any("mill" in name for name in names))

    def test_package_is_under_2500_lines(self):
        total = 0
        for path in BRW_DIR.glob("*.py"):
            total += path.read_text().count("\n")
        total += (REPO / "tests" / "test_brw.py").read_text().count("\n")
        self.assertLessEqual(total, 2500)


class BrwContract(unittest.TestCase):
    def test_factory_matches_reviewed_brw_prefix(self):
        self.assertEqual(FACTORY, "browser-tool-use-factory")
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[FAMILY_PREFIX], FACTORY)
        self.assertEqual(GEN, "grok-4.6")
        self.assertEqual(SOURCE_MILL_ID, "brw-mill-r193")
        self.assertEqual(SOURCE_ROUND, 193)
        self.assertEqual(CATALOG_FIRST, 193)
        self.assertEqual((MIN_STEPS, MAX_STEPS), (13, 16))
        self.assertEqual(len(BANNED_CSS), 37)
        self.assertEqual(len(BANNED_HOSTS), 176)
        self.assertIn("thought", BANNED)


class BrwCatalog(unittest.TestCase):
    def test_sixteen_unique_pairs(self):
        self.assertEqual(len(catalog.PAIRS), 16)
        self.assertEqual(catalog.slugs(), EXPECTED_OK_SLUGS)
        self.assertEqual(len(set(catalog.slugs())), 16)
        self.assertEqual(len({pair["bad_slug"] for pair in catalog.PAIRS}), 16)
        hosts = {pair["ok_host"] for pair in catalog.PAIRS} | {
            pair["bad_host"] for pair in catalog.PAIRS
        }
        self.assertTrue(hosts.isdisjoint(BANNED_HOSTS))

    def test_pair_lookup_and_refusals(self):
        self.assertEqual(catalog.pair_at(0)["ok_slug"], "branleat-offset-anchor")
        self.assertEqual(catalog.pair_for_round(193)["css_short"], "offset-anchor")
        self.assertEqual(catalog.pair_by_ok_slug("hornbeam-nth-of")["code"], 422)
        with self.assertRaises(BrwError):
            catalog.pair_at(-1)
        with self.assertRaises(BrwError):
            catalog.pair_at(True)  # type: ignore[arg-type]
        with self.assertRaises(BrwError):
            catalog.pair_by_ok_slug("not-a-pair")
        with self.assertRaises(BrwError):
            catalog.pair_for_round(192)


class BrwGenerate(unittest.TestCase):
    def test_success_is_brw_prefix_designed_episode(self):
        ok, bad = generate.pair_records(193)
        self.assertEqual(mill_prefix(ok), "brw")
        self.assertEqual(ok["id"], "brw-r193-branleat-offset-anchor")
        self.assertEqual(bad["id"], "brw-r193-coppermere-oa-410")
        self.assertEqual(ok["meta"]["factory"], FACTORY)
        self.assertEqual(ok["meta"]["round"], 193)
        self.assertEqual(ok["meta"]["generator"], GEN)
        self.assertTrue(ok["reward"]["success"])
        self.assertFalse(bad["reward"]["success"])
        self.assertTrue(MIN_STEPS <= len(ok["steps"]) <= MAX_STEPS)
        self.assertEqual(len(bad["steps"]), 13)
        self.assertEqual(
            [step["tool_call"]["name"] for step in ok["steps"]],
            list(SHIFT_SUCCESS_TOOLS),
        )
        self.assertEqual(
            [step["tool_call"]["name"] for step in bad["steps"]],
            list(FAIL_TOOLS),
        )
        for record in (ok, bad):
            blob = json.dumps(record["steps"])
            for banned in BANNED:
                self.assertNotIn(f'"{banned}"', blob)
        self.assertFalse(any("reward" in step for step in ok["steps"]))
        self.assertNotIn("http_409s", json.dumps(bad))
        self.assertIn("Novel coverage: 16%", generate.notes_for(193, catalog.pair_at(0)))

    def test_every_pair_validates(self):
        window = generate.generate_window(193)
        self.assertEqual(len(window), 16)
        self.assertEqual(window[0][0]["meta"]["round"], 193)
        self.assertEqual(window[-1][1]["meta"]["round"], 208)
        for ok, bad in window:
            self.assertEqual(mill_prefix(ok), "brw")
            self.assertEqual(mill_prefix(bad), "brw")
            self.assertTrue(ok["reward"]["success"])
            self.assertFalse(bad["reward"]["success"])
            self.assertTrue(MIN_STEPS <= len(ok["steps"]) <= MAX_STEPS)
            self.assertEqual(len(bad["steps"]), 13)
            self.assertNotEqual(bad["meta"]["seed"], ok["meta"]["seed"])

    def test_backface_visual_inserts_rotate_step(self):
        pair = catalog.pair_by_ok_slug("brimstone-backface")
        ok = generate.build_success(205, pair)
        names = [step["tool_call"]["name"] for step in ok["steps"]]
        self.assertGreaterEqual(len(names), 15)
        self.assertIn("browser_click", names)
        self.assertEqual(ok["steps"][7]["tool_call"]["args"]["ref"], "e4")

    def test_invalid_round_is_refused(self):
        with self.assertRaises(BrwError):
            generate.pair_records(0)
        with self.assertRaises(BrwError):
            generate.pair_records(True)  # type: ignore[arg-type]
        with self.assertRaises(BrwError):
            generate.pair_records(209)


class BrwAstExtract(unittest.TestCase):
    def test_catalog_matches_legacy_literals_without_exec(self):
        try:
            legacy = _legacy_literals()
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.skipTest("origin/legacy-mill-lane is not fetched")
        self.assertEqual(legacy["FACTORY"], FACTORY)
        self.assertEqual(legacy["GEN"], GEN)
        self.assertEqual(legacy["CATALOG_FIRST"], CATALOG_FIRST)
        self.assertEqual(frozenset(legacy["BANNED_HOSTS"]), BANNED_HOSTS)
        self.assertEqual(tuple(legacy["BANNED_CSS"]), BANNED_CSS)
        self.assertEqual([pair["ok_slug"] for pair in legacy["PAIRS"]], list(EXPECTED_OK_SLUGS))
        for extracted, pair in zip(legacy["PAIRS"], catalog.PAIRS, strict=True):
            self.assertEqual(extracted, dict(pair))
        names = _legacy_function_names()
        self.assertIn("build_success", names)
        self.assertIn("build_fail", names)
        self.assertIn("write_round", names)
        self.assertNotIn("write_round", generate.__all__)


class BrwCli(unittest.TestCase):
    def test_catalog_lists_pairs(self):
        code, out, err = invoke(["catalog"])
        self.assertEqual((code, err), (0, ""))
        self.assertIn("brw-mill-r193", out)
        self.assertIn("branleat-offset-anchor", out)
        self.assertIn("hornbeam-nth-of", out)

    def test_catalog_json_is_exact(self):
        code, out, err = invoke(["catalog", "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["source"], "brw-mill-r193")
        self.assertEqual(payload["factory"], FACTORY)
        self.assertEqual(len(payload["plants"]), 16)

    def test_generate_one_pair(self):
        code, out, err = invoke(["generate", "--round", "193"])
        self.assertEqual((code, err), (0, ""))
        lines = [line for line in out.splitlines() if line]
        self.assertEqual(len(lines), 2)
        ok, bad = json.loads(lines[0]), json.loads(lines[1])
        self.assertEqual(ok["id"], "brw-r193-branleat-offset-anchor")
        self.assertEqual(bad["id"], "brw-r193-coppermere-oa-410")
        self.assertEqual(len(ok["steps"]), 14)

    def test_generate_success_only(self):
        code, out, err = invoke(["generate", "--round", "193", "--success"])
        self.assertEqual((code, err), (0, ""))
        lines = [line for line in out.splitlines() if line]
        self.assertEqual(len(lines), 1)
        self.assertTrue(json.loads(lines[0])["reward"]["success"])

    def test_generate_window(self):
        code, out, err = invoke(["generate", "--window", "--round", "193"])
        self.assertEqual((code, err), (0, ""))
        lines = [line for line in out.splitlines() if line]
        self.assertEqual(len(lines), 32)
        self.assertEqual(json.loads(lines[-1])["meta"]["round"], 208)

    def test_unknown_slug_is_exit_two(self):
        code, out, err = invoke(["generate", "--round", "193", "--slug", "nope"])
        self.assertEqual((code, out), (2, ""))
        self.assertTrue(err.startswith("unknown_pair:"), err)

    def test_notes_command(self):
        code, out, err = invoke(["notes", "--round", "193"])
        self.assertEqual((code, err), (0, ""))
        self.assertIn("Novel coverage: 16%", out)
        self.assertIn("brw-r193-branleat-offset-anchor", out)


if __name__ == "__main__":
    unittest.main()
