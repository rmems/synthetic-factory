#!/usr/bin/env python3
"""Inventory completeness, unclassified-script guard, and archived import graph."""

from __future__ import annotations

import contextlib
import copy
import shutil
import json
import tempfile
from unittest.mock import patch
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
GIT = shutil.which("git")
if GIT is None:
    raise RuntimeError("git is required for inventory integration tests")
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import mill_script_inventory as msi  # noqa: E402


def _git_ignored(path: str) -> bool:
    result = subprocess.run(
        [GIT, "check-ignore", "--no-index", "-q", path],
        cwd=REPO,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


@contextlib.contextmanager
def _scope_repo():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        subprocess.run([GIT, "init", "-q", str(root)], check=True)
        shutil.copy(REPO / ".gitignore", root / ".gitignore")
        (root / ".qlty").mkdir()
        shutil.copy(REPO / ".qlty/qlty.toml", root / ".qlty/qlty.toml")
        yield root


class InventoryLoad(unittest.TestCase):
    def test_committed_inventory_is_loaded_and_bound_to_its_exact_bytes(self):
        self.assertEqual(msi.INVENTORY_BYTES, msi.INVENTORY_PATH.read_bytes())
        self.assertEqual(msi.INVENTORY["schema_version"], msi.SCHEMA_VERSION)
        self.assertEqual(
            msi.INVENTORY["historical_generator_policy"]["provenance_ref"],
            "origin/legacy-mill-lane",
        )

    def test_duplicate_key_and_wrong_schema_fail_closed(self):
        with self.assertRaisesRegex(msi.MillScriptInventoryError, "duplicate key"):
            msi.load_inventory_bytes(b'{"schema_version":"x","schema_version":"y"}\n')
        with self.assertRaisesRegex(msi.MillScriptInventoryError, "schema_version"):
            msi.load_inventory_bytes(b'{"schema_version":"other"}\n')

    def test_archive_pin_and_paths_are_validated(self):
        for key, value in (("provenance_commit", "main"), ("archived_paths", ["../outside.py"])):
            with self.subTest(key=key):
                document = json.loads(msi.INVENTORY_BYTES)
                document["historical_generator_policy"][key] = value
                with self.assertRaises(msi.MillScriptInventoryError):
                    msi.load_inventory_bytes(json.dumps(document).encode())


class Completeness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tracked = msi.tracked_paths(REPO)
        cls.inventory = msi.INVENTORY

    def test_every_matching_tracked_script_is_classified(self):
        missing = msi.unclassified_paths(self.tracked, self.inventory)
        self.assertEqual(missing, ())

    def test_every_inventory_script_is_tracked_and_has_an_owner(self):
        tracked = frozenset(self.tracked)
        for row in self.inventory["scripts"]:
            with self.subTest(path=row["path"]):
                self.assertIn(row["path"], tracked)
                self.assertTrue(row["owner"])
                self.assertIn(row["classification"], msi.CLASSIFICATIONS)
                expected = "production" if row["classification"] == "production" else "archived"
                self.assertEqual(row["quality_scope"], expected)

    def test_mill_family_owners_exist_on_main(self):
        for row in self.inventory["mill_families"]:
            with self.subTest(family=row["family"]):
                self.assertEqual(row["classification"], "production")
                owner = REPO / row["owner"]
                self.assertTrue(owner.exists(), row["owner"])

    def test_historical_examples_match_the_guard_patterns(self):
        examples = self.inventory["historical_generator_policy"]["example_paths"]
        matched = msi.matching_paths(examples, self.inventory["match_patterns"])
        self.assertEqual(matched, tuple(sorted(examples)))


class UnclassifiedGuard(unittest.TestCase):
    def test_a_new_matching_script_fails_until_it_is_classified(self):
        tracked = msi.tracked_paths(REPO) + ("pipelines/brand_new_leftover_mill.py",)
        missing = msi.unclassified_paths(tracked, msi.INVENTORY)
        self.assertEqual(missing, ("pipelines/brand_new_leftover_mill.py",))

    def test_check_inventory_fails_closed_on_an_unclassified_script(self):
        report = msi.check_inventory(
            REPO,
            tracked=msi.tracked_paths(REPO) + ("scripts/tmp_mill/gen.py",),
        )
        self.assertIn("scripts/tmp_mill/gen.py", report["unclassified"])
        self.assertFalse(report["ok"])

    def test_committed_tree_check_is_clean(self):
        report = msi.check_inventory(REPO)
        self.assertEqual(report["unclassified"], ())
        self.assertEqual(report["gitignore_hits_on_production"], ())
        self.assertEqual(report["qlty_hits_on_production"], ())
        self.assertEqual(report["missing_gitignore_patterns"], ())
        self.assertEqual(report["missing_qlty_patterns"], ())
        self.assertEqual(report["forbidden_blanket_patterns_present"], ())
        self.assertTrue(report["ok"])


class QualityScope(unittest.TestCase):
    def test_gitignore_does_not_suppress_production_mill_modules(self):
        for path in (
            "pipelines/leftover_mill.py",
            "pipelines/compose_mill.py",
            "pipelines/training_audit_mill.py",
            "pipelines/mill_family.py",
            "tests/test_leftover_mill.py",
            "experiments/2026-08-19-quality-report.md",
        ):
            with self.subTest(path=path):
                self.assertFalse(_git_ignored(path), path)

    def test_gitignore_isolates_archived_generator_paths(self):
        for path in (
            "experiments/srl_r6110_leftover3_mill.py",
            "experiments/nested/wsr-mill-leftover3-r41.py",
            "experiments/_gen_obs_leftover10.py",
            "scripts/foo_mill.py",
            "mill_acm_r1.py",
        ):
            with self.subTest(path=path):
                self.assertTrue(_git_ignored(path), path)

    def test_qlty_excludes_do_not_hit_production_inventory_paths(self):
        hits = msi.patterns_hitting(
            msi.INVENTORY["quality_policy"]["archived_exclude_patterns"],
            msi.production_script_paths(msi.INVENTORY),
        )
        self.assertEqual(hits, ())


class ScopeRegressions(unittest.TestCase):
    def test_added_gitignore_rule_cannot_hide_production(self):
        with _scope_repo() as root:
            path = root / ".gitignore"
            path.write_text(path.read_text() + "\npipelines/leftover_mill.py\n")
            report = msi.check_inventory(root, tracked=())
        self.assertFalse(report["ok"])
        self.assertIn(
            ("pipelines/leftover_mill.py", "pipelines/leftover_mill.py"),
            report["gitignore_hits_on_production"],
        )

    def test_production_reinclusion_is_not_reported_as_ignored(self):
        production = "pipelines/leftover_mill.py"
        with _scope_repo() as root:
            path = root / ".gitignore"
            path.write_text(path.read_text() + "\n" + production + "\n!" + production + "\n")
            report = msi.check_inventory(root, tracked=())
        self.assertEqual(report["gitignore_hits_on_production"], ())
        self.assertTrue(report["ok"])

    def test_archived_reinclusion_is_not_reported_as_ignored(self):
        archived = "experiments/ewr_leftover3_mill.py"
        with _scope_repo() as root:
            path = root / ".gitignore"
            path.write_text(path.read_text() + "\n!" + archived + "\n")
            report = msi.check_inventory(root, tracked=())
        self.assertFalse(report["ok"])
        self.assertIn(archived, report["uncovered_gitignore_archived_paths"])
        evidence = next(row for row in report["gitignore_rule_evidence"] if row[0] == archived)
        self.assertEqual(evidence[1], ".gitignore")
        self.assertTrue(evidence[2].isdigit())
        self.assertEqual(evidence[3], "!" + archived)

    def test_added_qlty_rule_cannot_hide_production(self):
        rules = msi.qlty_exclude_patterns(REPO) + ("**/*_mill.py",)
        with patch.object(msi, "qlty_exclude_patterns", return_value=rules):
            report = msi.check_inventory(REPO)
        self.assertFalse(report["ok"])
        self.assertIn(
            ("**/*_mill.py", "pipelines/leftover_mill.py"), report["qlty_hits_on_production"]
        )

    def test_archived_row_must_be_covered_by_both_exclusion_files(self):
        inventory = copy.deepcopy(msi.INVENTORY)
        archived = dict(
            inventory["scripts"][0],
            path="pipelines/foo_mill.py",
            classification="retained_historical_generator",
            quality_scope="archived",
        )
        inventory["scripts"] += (archived,)
        report = msi.check_inventory(REPO, inventory=inventory)
        self.assertFalse(report["ok"])
        self.assertIn(archived["path"], report["uncovered_gitignore_archived_paths"])
        self.assertIn(archived["path"], report["uncovered_qlty_archived_paths"])

    def test_legacy_loops_are_matched_and_excluded(self):
        path = "experiments/rag-loop-r343.py"
        self.assertTrue(msi.matching_paths((path,), msi.INVENTORY["match_patterns"]))
        self.assertTrue(_git_ignored(path))
        self.assertTrue(msi.patterns_hitting(msi.qlty_exclude_patterns(REPO), (path,)))

    def test_archived_imports_include_nonexample_generators(self):
        archived = msi.archived_module_names(msi.INVENTORY)
        self.assertEqual(
            msi.archived_import_hits("import ewr_leftover3_mill", archived), ("ewr_leftover3_mill",)
        )
        paths = msi.INVENTORY["historical_generator_policy"]["archived_paths"]
        self.assertIn("experiments/rag-loop-r343.py", paths)

    def test_qlty_rules_use_toml_not_double_quote_line_splitting(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".qlty").mkdir()
            (root / ".qlty/qlty.toml").write_text(
                "exclude_patterns = ['pipelines/leftover_mill.py']\n"
            )
            self.assertEqual(msi.qlty_exclude_patterns(root), ("pipelines/leftover_mill.py",))


class ImportGraph(unittest.TestCase):
    def test_archived_module_helper_detects_a_leftover_mill_import(self):
        archived = msi.archived_module_names(msi.INVENTORY)
        self.assertIn("srl_r6110_leftover3_mill", archived)
        hits = msi.archived_import_hits(
            "import leftover_mill\nimport srl_r6110_leftover3_mill\n",
            archived,
        )
        self.assertEqual(hits, ("srl_r6110_leftover3_mill",))

    def test_production_entrypoints_do_not_import_archived_mills(self):
        archived = msi.archived_module_names(msi.INVENTORY)
        tracked = msi.tracked_paths(REPO)
        failures = []
        for relpath in msi.production_python_paths(tracked):
            source = (REPO / relpath).read_text(encoding="utf-8")
            hits = msi.archived_import_hits(source, archived)
            if hits:
                failures.append((relpath, hits))
        self.assertEqual(failures, [])

    def test_production_consumers_still_import_leftover_mill(self):
        publisher = (REPO / "scripts" / "publish_grok46_hub.py").read_text(encoding="utf-8")
        preferences = (REPO / "pipelines" / "curate_preferences.py").read_text(encoding="utf-8")
        names = msi.imported_module_names(publisher) | msi.imported_module_names(preferences)
        self.assertIn("leftover_mill", names)


class Cli(unittest.TestCase):
    def test_check_cli_exits_zero_on_the_committed_tree(self):
        result = subprocess.run(
            [sys.executable, str(PIPELINES / "mill_script_inventory.py"), "--check"],
            cwd=REPO,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])


if __name__ == "__main__":
    unittest.main()
