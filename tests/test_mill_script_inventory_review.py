"""Inventory review regressions for canonical paths and complete policy scope."""

import copy
import json
import unittest
from unittest.mock import patch

from tests.test_mill_script_inventory import REPO, _scope_repo, msi


class CanonicalPaths(unittest.TestCase):
    def test_noncanonical_path_components_are_refused(self):
        for path in ("./pipelines/foo_mill.py", "pipelines/./foo_mill.py",
                     "pipelines//foo_mill.py", "."):
            with self.subTest(path=path):
                document = json.loads(msi.INVENTORY_BYTES)
                document["scripts"][0]["path"] = path
                with self.assertRaises(msi.MillScriptInventoryError):
                    msi.load_inventory_bytes(json.dumps(document).encode())


class ArchivedCoverage(unittest.TestCase):
    def test_every_pinned_archived_path_matches_classification_guard(self):
        paths = msi.historical_paths(msi.INVENTORY)
        self.assertEqual(msi.uncovered_paths(msi.INVENTORY["match_patterns"], paths), ())

    def test_additional_loop_publishers_are_classified_and_excluded(self):
        paths = ("experiments/dbc-hop-loop.py", "experiments/dpr_loop_r2850.py",
                 "experiments/ntp-loop-unique-lll.py", "experiments/dbc-hop-qbp-r74.py")
        self.assertTrue(set(paths).issubset(msi.historical_paths(msi.INVENTORY)))
        self.assertEqual(msi.uncovered_paths(msi.INVENTORY["match_patterns"], paths), ())
        self.assertEqual(msi.uncovered_paths(msi.qlty_exclude_patterns(REPO), paths), ())
        self.assertEqual(msi._ignored_paths(msi.gitignore_matches(REPO, paths)), set(paths))

    def test_explicit_archived_script_remains_a_valid_classification(self):
        inventory = copy.deepcopy(msi.INVENTORY)
        archived = dict(inventory["scripts"][0], path="experiments/extra_mill.py",
                        classification="retained_historical_generator", quality_scope="archived")
        inventory["scripts"] += (archived,)
        with _scope_repo() as root:
            report = msi.check_inventory(root, inventory=inventory, tracked=(archived["path"],))
        self.assertTrue(report["ok"], report)


class RetainedScope(unittest.TestCase):
    def test_equivalent_git_blanket_rules_cannot_hide_retained_notes(self):
        note = "experiments/2026-08-19-quality-report.md"
        for rule in ("experiments/**", "/experiments/"):
            with self.subTest(rule=rule), _scope_repo() as root:
                path = root / ".gitignore"
                path.write_text(path.read_text() + "\n" + rule + "\n")
                report = msi.check_inventory(root, tracked=(note,))
                self.assertFalse(report["ok"], report)

    def test_equivalent_qlty_blanket_rule_cannot_hide_retained_notes(self):
        note = "experiments/2026-08-19-quality-report.md"
        rules = msi.qlty_exclude_patterns(REPO) + ("experiments/**",)
        with patch.object(msi, "qlty_exclude_patterns", return_value=rules):
            report = msi.check_inventory(REPO, tracked=(note,))
        self.assertFalse(report["ok"], report)


class ImportAliases(unittest.TestCase):
    def test_reviewed_production_package_is_not_confused_with_archived_basename(self):
        archived = msi.archived_module_names(msi.INVENTORY)
        self.assertEqual(msi.archived_import_hits("from mill import cli", archived), ())

    def test_qualified_archived_module_remains_blocked(self):
        archived = msi.archived_module_names(msi.INVENTORY)
        self.assertIn("scripts.infra_as_code_mill.mill",
                      msi.archived_import_hits("import scripts.infra_as_code_mill.mill", archived))

    def test_qualified_from_import_cannot_hide_archived_module(self):
        archived = msi.archived_module_names(msi.INVENTORY)
        statement = "from scripts.infra_as_code_mill import mill"
        self.assertIn("scripts.infra_as_code_mill.mill",
                      msi.archived_import_hits(statement, archived))

    def test_archived_package_initializer_is_bound_to_its_package_name(self):
        archived = msi.archived_module_names(msi.INVENTORY)
        self.assertIn("scripts.infra_as_code_mill",
                      msi.archived_import_hits("from scripts import infra_as_code_mill", archived))

    def test_relative_from_import_aliases_cannot_bypass_archived_guard(self):
        archived = msi.archived_module_names(msi.INVENTORY)
        for statement in ("from . import ewr_leftover3_mill",
                          "from .. import ewr_leftover3_mill as retired",
                          "from .helpers import ewr_leftover3_mill"):
            with self.subTest(statement=statement):
                self.assertEqual(msi.archived_import_hits(statement, archived),
                                 ("ewr_leftover3_mill",))


class FamilyOwnership(unittest.TestCase):
    def test_removing_an_existing_family_owner_fails_the_guard(self):
        inventory = copy.deepcopy(msi.INVENTORY)
        inventory["mill_families"] = tuple(
            row for row in inventory["mill_families"] if row["family"] != "crp"
        )
        self.assertFalse(msi.check_inventory(REPO, inventory=inventory)["ok"])

    def test_active_archived_families_have_reviewed_cleaned_owners(self):
        owners = {row["family"]: row["owner"] for row in msi.INVENTORY["mill_families"]}
        for family in ("lhc", "dpr", "dbc", "ntp", "ssr"):
            with self.subTest(family=family):
                self.assertEqual(owners.get(family), f"pipelines/{family}")


class PublisherAndFamilyScope(unittest.TestCase):
    def test_chain_and_pub_publishers_are_classified_and_excluded(self):
        paths = ("experiments/dbc-chain-after-1125.py", "experiments/ntp-chain-llll15-26.py",
                 "experiments/irc-pub-r5001.py")
        self.assertTrue(set(paths).issubset(msi.historical_paths(msi.INVENTORY)))
        self.assertEqual(msi.uncovered_paths(msi.INVENTORY["match_patterns"], paths), ())
        self.assertEqual(msi.uncovered_paths(msi.qlty_exclude_patterns(REPO), paths), ())
        self.assertEqual(msi._ignored_paths(msi.gitignore_matches(REPO, paths)), set(paths))

    def test_gitignore_cannot_hide_cleaned_production_family_package(self):
        paths = ("pipelines/mill/__init__.py", "pipelines/mill/cli.py")
        with _scope_repo() as root:
            ignore = root / ".gitignore"
            ignore.write_text(ignore.read_text() + "\npipelines/mill/\n")
            report = msi.check_inventory(root, tracked=paths)
        self.assertFalse(report["ok"], report)
        self.assertEqual({path for _, path in report["gitignore_hits_on_production"]}, set(paths))

    def test_qlty_cannot_hide_cleaned_production_family_package(self):
        paths = ("pipelines/mill/__init__.py", "pipelines/mill/cli.py")
        rules = msi.qlty_exclude_patterns(REPO) + ("pipelines/mill/**",)
        with patch.object(msi, "qlty_exclude_patterns", return_value=rules):
            report = msi.check_inventory(REPO, tracked=paths)
        self.assertFalse(report["ok"], report)
        self.assertEqual({path for _, path in report["qlty_hits_on_production"]}, set(paths))
