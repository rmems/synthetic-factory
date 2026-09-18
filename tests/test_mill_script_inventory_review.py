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

    def test_nested_gitignore_cannot_hide_cleaned_production_family_package(self):
        paths = ("pipelines/mill/__init__.py", "pipelines/mill/cli.py")
        with _scope_repo() as root:
            (root / "pipelines").mkdir()
            (root / "pipelines" / ".gitignore").write_text("mill/**\n")
            report = msi.check_inventory(root, tracked=paths)
            matches = msi.gitignore_matches(root, (*paths, "pipelines/will/cli.py"))
        self.assertFalse(report["ok"], report)
        self.assertEqual({path for _, path in report["gitignore_hits_on_production"]}, set(paths))
        self.assertNotIn("pipelines/will/cli.py", matches)

    def test_gitignore_bracket_class_cannot_hide_production_mill_package(self):
        paths = ("pipelines/mill/__init__.py", "pipelines/mill/cli.py")
        with _scope_repo() as root:
            ignore = root / ".gitignore"
            ignore.write_text(ignore.read_text() + "\npipelines/[m]ill/**\n")
            report = msi.check_inventory(root, tracked=paths)
            matches = msi.gitignore_matches(root, (*paths, "pipelines/will/cli.py"))
        self.assertFalse(report["ok"], report)
        self.assertEqual({path for _, path in report["gitignore_hits_on_production"]}, set(paths))
        self.assertNotIn("pipelines/will/cli.py", matches)

    def test_escaped_gitignore_bracket_is_literal(self):
        with _scope_repo() as root:
            (root / ".gitignore").write_text("pipelines/\\[m]ill/**\n")
            matches = msi.gitignore_matches(
                root, ("pipelines/mill/cli.py", "pipelines/[m]ill/cli.py")
            )
        self.assertNotIn("pipelines/mill/cli.py", matches)
        self.assertIn("pipelines/[m]ill/cli.py", matches)

    def test_qlty_cannot_hide_cleaned_production_family_package(self):
        paths = ("pipelines/mill/__init__.py", "pipelines/mill/cli.py")
        rules = msi.qlty_exclude_patterns(REPO) + ("pipelines/mill/**",)
        with patch.object(msi, "qlty_exclude_patterns", return_value=rules):
            report = msi.check_inventory(REPO, tracked=paths)
        self.assertFalse(report["ok"], report)
        self.assertEqual({path for _, path in report["qlty_hits_on_production"]}, set(paths))


class InventoryIntegrity(unittest.TestCase):
    def test_archive_deletion_or_commit_substitution_fails_the_guard(self):
        for field, change in (("archived_paths", lambda paths: tuple(
            path for path in paths if path != "experiments/_gen_acm_plants_r4230.py")),
                              ("provenance_commit", lambda _: "0" * 40)):
            with self.subTest(field=field):
                inventory = copy.deepcopy(msi.INVENTORY)
                policy = inventory["historical_generator_policy"]
                policy[field] = change(policy[field])
                self.assertFalse(msi.check_inventory(REPO, inventory=inventory)["ok"])
                with self.assertRaises(msi.MillScriptInventoryError):
                    msi.load_inventory_bytes(json.dumps(inventory).encode())

    def test_literal_dynamic_imports_cannot_load_archived_publishers(self):
        statements = (
            'importlib.import_module("experiments.ewr_leftover3_mill")',
            '__import__("ewr_leftover3_mill")',
            'from builtins import __import__ as load; load("ewr_leftover3_mill")',
            'import importlib as loader; loader.import_module("ewr_leftover3_mill")',
            'from importlib import import_module as load; load(name="ewr_leftover3_mill")',
            'import importlib; load = importlib.import_module; load("experiments.ewr_leftover3_mill")',
            'import importlib; load = importlib.import_module; other = load; other("ewr_leftover3_mill")',
            'from importlib import import_module; load: object = import_module; load("ewr_leftover3_mill")',
        )
        archived = msi.archived_module_names(msi.INVENTORY)
        for source in statements:
            with self.subTest(source=source):
                self.assertTrue(msi.archived_import_hits(source, archived))

    def test_secondary_cleaned_owners_are_required_and_protected(self):
        for owner in ("pipelines/lhc_w4cl", "pipelines/code_leftover3",
                      "pipelines/maos", "pipelines/ttf", "pipelines/nelb"):
            with self.subTest(owner=owner):
                rules = msi.qlty_exclude_patterns(REPO) + (owner + "/**",)
                with patch.object(msi, "qlty_exclude_patterns", return_value=rules):
                    self.assertFalse(msi.check_inventory(REPO)["ok"])
                inventory = copy.deepcopy(msi.INVENTORY)
                inventory["mill_families"] = tuple(
                    row for row in inventory["mill_families"] if row["owner"] != owner
                )
                self.assertFalse(msi.check_inventory(REPO, inventory=inventory)["ok"])


class CompleteProductionAndImportScope(unittest.TestCase):
    def test_nonarchive_production_owners_cannot_disappear(self):
        for owner in ("pipelines/actf", "pipelines/ffpc", "pipelines/maos",
                      "pipelines/ttf", "pipelines/nelb"):
            with self.subTest(owner=owner):
                inventory = copy.deepcopy(msi.INVENTORY)
                inventory["mill_families"] = tuple(
                    row for row in inventory["mill_families"] if row["owner"] != owner
                )
                self.assertFalse(msi.check_inventory(REPO, inventory=inventory)["ok"])

    def test_literal_hyphenated_dynamic_imports_are_archived(self):
        archived = msi.archived_module_names(msi.INVENTORY)
        for name in ("rag-loop-r343", "experiments.rag-loop-r343"):
            with self.subTest(name=name):
                self.assertIn(name, msi.archived_import_hits(f'importlib.import_module("{name}")', archived))

    def test_bare_archived_package_import_is_blocked(self):
        archived = msi.archived_module_names(msi.INVENTORY)
        self.assertIn("infra_as_code_mill", msi.archived_import_hits("import infra_as_code_mill", archived))

    def test_inventory_helper_modules_cannot_be_excluded(self):
        paths = (
            "pipelines/mill_script_inventory_schema.py",
            "pipelines/mill_script_inventory_families.py",
            "pipelines/mill_script_inventory_git.py",
        )
        for path in paths:
            with self.subTest(path=path), _scope_repo() as root:
                ignore = root / ".gitignore"
                ignore.write_text(ignore.read_text() + "\n" + path + "\n")
                self.assertFalse(msi.check_inventory(root, tracked=paths)["ok"])
                rules = msi.qlty_exclude_patterns(REPO) + (path,)
                with patch.object(msi, "qlty_exclude_patterns", return_value=rules):
                    self.assertFalse(msi.check_inventory(REPO, tracked=paths)["ok"])
