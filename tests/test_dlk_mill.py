#!/usr/bin/env python3
"""The dlk mill family home under ``pipelines/dlk/`` (cleaned package).

``dlk_r1214_leftover3_mill.py`` and ``dlk_r1280_leftover3_mill.py`` were
preserved on ``legacy-mill-lane``. The prior ``cursor/mill-dlk-4162`` branch
vendored those two raw scripts straight into ``pipelines/dlk/``; this cleaned
package replaces that dump with a catalog (``config/dlk/``) plus pure builders
(``pipelines/dlk/``) and drops the exec path. These tests pin identity, record
shape and the no-exec contract without publishing a raw round.
"""

import ast
import io
import json
import subprocess
import sys
import unittest
from pathlib import Path
from typing import ClassVar

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from dlk import (
    cli,  # noqa: E402
    generate,  # noqa: E402
)
from dlk._contract import EXPECTED, FACTORY, GEN, N_ROUNDS, PREFIX, PRESERVED_ROUNDS  # noqa: E402
from dlk.catalog import load_all, load_catalog  # noqa: E402
from mill_family import REVIEWED_MILL_PREFIX_HOMES, mill_prefix  # noqa: E402


class DlkContract(unittest.TestCase):
    def test_factory_matches_reviewed_dlk_prefix_home(self):
        self.assertEqual(PREFIX, "dlk")
        self.assertEqual(FACTORY, "distributed-lock-factory")
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES["dlk"], FACTORY)
        self.assertEqual(GEN, "grok-4.6")
        self.assertEqual(N_ROUNDS, 16)
        self.assertEqual(EXPECTED, 2)
        self.assertEqual(PRESERVED_ROUNDS, (1214, 1280))


class DlkCatalog(unittest.TestCase):
    def test_two_preserved_rounds_each_with_sixteen_unique_plants(self):
        catalogs = load_all()
        self.assertEqual([c.round for c in catalogs], [1214, 1280])
        for catalog in catalogs:
            self.assertEqual(catalog.factory, FACTORY)
            self.assertEqual(catalog.generator, GEN)
            self.assertEqual(len(catalog.plants), 16)
            self.assertEqual(len(set(catalog.slugs)), 16)

    def test_plant_slugs_are_distinct_across_both_rounds(self):
        catalogs = load_all()
        all_slugs = [slug for c in catalogs for slug in c.slugs]
        self.assertEqual(len(all_slugs), 32)
        self.assertEqual(len(set(all_slugs)), 32)

    def test_every_plant_carries_the_fourteen_legacy_keys(self):
        for catalog in load_all():
            for plant in catalog.plants:
                for key in ("slug", "seed", "why", "bad", "fix", "dump", "src",
                            "test", "probe", "cli", "leftover_fn", "ok_pat",
                            "fail_slug", "fail_why"):
                    self.assertTrue(getattr(plant, key), f"{plant.slug} missing {key}")

    def test_load_catalog_refuses_an_unknown_round(self):
        with self.assertRaises(KeyError):
            load_catalog(9999)


class DlkGenerate(unittest.TestCase):
    def test_success_ep_shape_and_identity(self):
        catalog = load_catalog(1214)
        plant = catalog.plants[0]
        record = generate.success_ep(1214, plant)
        self.assertEqual(record["id"], f"dlk-r1214-{plant.slug}")
        self.assertEqual(mill_prefix(record), "dlk")
        self.assertEqual(record["meta"], {"factory": FACTORY, "round": 1214, "generator": GEN})
        self.assertEqual(len(record["steps"]), generate.N_SUCCESS_STEPS)
        self.assertEqual(record["reward"],
                         {"success": True, "plan_changes": 1, "tests_passed": 4, "cost_steps": 16})
        self.assertTrue(record["steps"][0]["decision_basis"].startswith("Plan:"))
        for step in record["steps"]:
            self.assertIn("decision_basis", step)
            self.assertNotIn("reward", step)

    def test_fail_ep_shape_and_identity(self):
        catalog = load_catalog(1280)
        plant = catalog.plants[0]
        record = generate.fail_ep(1280, plant)
        self.assertEqual(record["id"], f"dlk-r1280-{plant.fail_slug}")
        self.assertEqual(mill_prefix(record), "dlk")
        self.assertEqual(record["meta"], {"factory": FACTORY, "round": 1280, "generator": GEN})
        self.assertEqual(len(record["steps"]), generate.N_FAIL_STEPS)
        self.assertEqual(record["reward"],
                         {"success": False, "plan_changes": 1, "tests_passed": 3,
                          "xfailed": 1, "handoff": 1, "cost_steps": 17})

    def test_notes_markdown_carries_novel_coverage_and_seed(self):
        catalog = load_catalog(1214)
        plant = catalog.plants[0]
        s = generate.success_ep(1214, plant)
        f = generate.fail_ep(1214, plant)
        text = generate.notes(1214, plant, s, f)
        self.assertIn("# NOTES-r1214 distributed-lock-factory", text)
        self.assertIn("Novel coverage:", text)
        self.assertIn(plant.seed, text)
        self.assertIn(s["id"], text)
        self.assertIn(f["id"], text)

    def test_success_and_fail_ids_partition_a_round(self):
        catalog = load_catalog(1214)
        success_ids = [f"dlk-r1214-{p.slug}" for p in catalog.plants]
        fail_ids = [f"dlk-r1214-{p.fail_slug}" for p in catalog.plants]
        self.assertEqual(len(set(success_ids) & set(fail_ids)), 0)
        self.assertEqual(len(success_ids) + len(fail_ids), 32)


class DlkNeverExec(unittest.TestCase):
    """The legacy ``txn``/``main`` exec path must not be carried into the package."""

    BANNED_IMPORTS: ClassVar[set[str]] = {"subprocess"}
    BANNED_DEFS: ClassVar[set[str]] = {"txn", "main"}

    def test_no_banned_imports_or_defs_in_package_modules(self):
        package_dir = REPO / "pipelines" / "dlk"
        findings = []
        for path in sorted(package_dir.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split(".")[0] in self.BANNED_IMPORTS:
                            findings.append((path.name, "import", alias.name))
                elif (isinstance(node, ast.ImportFrom) and node.module
                      and node.module.split(".")[0] in self.BANNED_IMPORTS):
                    findings.append((path.name, "import", node.module))
                elif (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                      and node.name in self.BANNED_DEFS):
                    findings.append((path.name, "def", node.name))
        self.assertEqual(findings, [], f"banned exec surface found: {findings}")

    def test_generate_has_no_main_guard(self):
        path = REPO / "pipelines" / "dlk" / "generate.py"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotEqual(alias.name.split(".")[0], "subprocess",
                                         "generate.py must not import subprocess")
            elif isinstance(node, ast.ImportFrom):
                self.assertNotEqual(
                    node.module and node.module.split(".")[0], "subprocess",
                    "generate.py must not import subprocess")
            elif isinstance(node, ast.If):
                test_src = ast.unparse(node.test)
                self.assertNotIn('__name__', test_src.replace('"', "'"),
                                 "generate.py must not carry a __main__ guard")


class DlkCli(unittest.TestCase):
    def _run(self, *argv):
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = cli.run(list(argv))
        return code, buf.getvalue()

    def test_catalog_command_prints_both_rounds(self):
        code, out = self._run("catalog")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["command"], "catalog")
        self.assertEqual(payload["index"]["prefix"], "dlk")
        self.assertEqual(sorted(payload["index"]["preserved_rounds"]), [1214, 1280])

    def test_show_success_builds_record_in_memory(self):
        code, out = self._run("show", "--round", "1214", "--index", "0", "--kind", "success")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        record = payload["record"]
        self.assertTrue(record["id"].startswith("dlk-r1214-"))
        self.assertEqual(record["meta"]["factory"], "distributed-lock-factory")

    def test_show_fail_builds_record_in_memory(self):
        code, out = self._run("show", "--round", "1280", "--index", "0", "--kind", "fail")
        self.assertEqual(code, 0)
        record = json.loads(out)["record"]
        self.assertEqual(record["reward"]["success"], False)
        self.assertEqual(record["reward"]["handoff"], 1)

    def test_show_notes_prints_markdown(self):
        code, out = self._run("show", "--round", "1214", "--index", "0", "--kind", "notes")
        self.assertEqual(code, 0)
        self.assertIn("# NOTES-r1214 distributed-lock-factory", out)
        self.assertIn("Novel coverage:", out)

    def test_audit_command_is_clean(self):
        code, out = self._run("audit")
        payload = json.loads(out)
        self.assertEqual(payload["command"], "audit")
        self.assertEqual(payload["status"], "ok", f"audit findings: {payload.get('findings')}")
        self.assertEqual(code, 0)
        self.assertEqual(sorted(payload["rounds"]), [1214, 1280])
        self.assertEqual(payload["plants"], 32)


class DlkFidelityToLegacy(unittest.TestCase):
    """Optionally prove the cleaned builders reproduce the legacy records byte-for-byte.

    Skips when ``origin/legacy-mill-lane`` is not fetchable (e.g. a CI checkout
    without the preserved branch). The legacy ``success_ep``/``fail_ep``/``notes``
    are pure (no subprocess); only ``txn``/``main`` exec, and those are not
    loaded here.
    """

    LEGACY_FILES: ClassVar[dict[int, str]] = {
        1214: "experiments/dlk_r1214_leftover3_mill.py",
        1280: "experiments/dlk_r1280_leftover3_mill.py",
    }

    def _legacy_module(self, round):
        path = self.LEGACY_FILES[round]
        proc = subprocess.run(
            ["git", "show", f"origin/legacy-mill-lane:{path}"],
            capture_output=True, text=True, cwd=str(REPO), check=False,
        )
        if proc.returncode != 0:
            self.skipTest(f"origin/legacy-mill-lane not available: {proc.stderr.strip()}")
        src = proc.stdout
        tree = ast.parse(src)
        keep = {"step", "success_ep", "fail_ep", "notes", "PLANTS"}
        namespace: dict = {}
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.Assign)) and getattr(node, "lineno", None):
                if isinstance(node, ast.FunctionDef) and node.name in keep:
                    exec(compile(ast.Module([node], []), "<legacy>", "exec"), namespace)  # noqa: S102
                elif isinstance(node, ast.Assign) and any(
                    isinstance(t, ast.Name) and t.id == "PLANTS" for t in node.targets
                ):
                    namespace["PLANTS"] = ast.literal_eval(node.value)
        return namespace

    def test_cleaned_records_match_legacy_byte_for_byte(self):
        for round in (1214, 1280):
            legacy = self._legacy_module(round)
            catalog = load_catalog(round)
            self.assertEqual(len(catalog.plants), len(legacy["PLANTS"]))
            for plant, legacy_plant in zip(catalog.plants, legacy["PLANTS"]):
                s_clean = generate.success_ep(round, plant)
                f_clean = generate.fail_ep(round, plant)
                s_legacy = legacy["success_ep"](round, legacy_plant)
                f_legacy = legacy["fail_ep"](round, legacy_plant)
                self.assertEqual(s_clean, s_legacy,
                                 f"success_ep drift at r{round} {plant.slug}")
                self.assertEqual(f_clean, f_legacy,
                                 f"fail_ep drift at r{round} {plant.slug}")
                n_clean = generate.notes(round, plant, s_clean, f_clean)
                n_legacy = legacy["notes"](round, legacy_plant, s_legacy, f_legacy)
                self.assertEqual(n_clean, n_legacy,
                                 f"notes drift at r{round} {plant.slug}")


if __name__ == "__main__":
    unittest.main()
