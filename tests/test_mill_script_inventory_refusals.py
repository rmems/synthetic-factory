"""Malformed inventories and unavailable exclusion evidence must fail closed."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.test_mill_script_inventory import REPO, msi


class InventorySchemaRefusals(unittest.TestCase):
    def test_invalid_encoded_documents_are_refused(self):
        for payload in (None, b" " * 256001, b"\xff", b"{", b"[]"):
            with self.subTest(payload_type=type(payload).__name__):
                with self.assertRaises(msi.MillScriptInventoryError):
                    msi.load_inventory_bytes(payload)

    def test_invalid_top_level_collections_are_refused(self):
        for field, value in (("scripts", None), ("scripts", []), ("mill_families", []),
                             ("match_patterns", []), ("notes", ""), ("quality_policy", [])):
            with self.subTest(field=field, value=value):
                document = json.loads(msi.INVENTORY_BYTES)
                document[field] = value
                with self.assertRaises(msi.MillScriptInventoryError):
                    msi.load_inventory_bytes(json.dumps(document).encode())

    def test_invalid_script_identity_and_scope_are_refused(self):
        cases = (("classification", "unknown"), ("quality_scope", "unknown"),
                 ("quality_scope", "archived"), ("canonical_replacement", 42),
                 ("path", "/outside.py"), ("owner", ""))
        for field, value in cases:
            with self.subTest(field=field):
                document = json.loads(msi.INVENTORY_BYTES)
                document["scripts"][0][field] = value
                with self.assertRaises(msi.MillScriptInventoryError):
                    msi.load_inventory_bytes(json.dumps(document).encode())

    def test_duplicate_script_coordinates_are_refused(self):
        document = json.loads(msi.INVENTORY_BYTES)
        document["scripts"].append(document["scripts"][0])
        with self.assertRaisesRegex(msi.MillScriptInventoryError, "unique"):
            msi.load_inventory_bytes(json.dumps(document).encode())

    def test_invalid_archive_and_family_policies_are_refused(self):
        cases = (("historical_generator_policy", "classification", "production"),
                 ("historical_generator_policy", "quality_scope", "production"),
                 ("mill_families", "classification", "unknown"))
        for group, field, value in cases:
            with self.subTest(group=group, field=field):
                document = json.loads(msi.INVENTORY_BYTES)
                row = document[group][0] if group == "mill_families" else document[group]
                row[field] = value
                with self.assertRaises(msi.MillScriptInventoryError):
                    msi.load_inventory_bytes(json.dumps(document).encode())


class InventoryEvidenceRefusals(unittest.TestCase):
    def test_missing_git_cannot_be_reported_as_clean_scope(self):
        with patch.object(msi, "_git_available", return_value=False):
            with self.assertRaisesRegex(msi.MillScriptInventoryError, "git is required"):
                msi.tracked_paths()

    def test_git_helper_refuses_commands_outside_the_allowlist(self):
        for arguments in ((), ("status",), ("ls-files",), ("check-ignore", "-z")):
            with self.subTest(arguments=arguments):
                with self.assertRaisesRegex(
                    msi.MillScriptInventoryError, "ls-files or check-ignore"
                ):
                    msi._git_output(REPO, arguments)

    def test_git_helper_lists_tracked_paths_from_the_index(self):
        tracked = msi.tracked_paths(REPO)
        self.assertIn("pipelines/mill_script_inventory.py", tracked)
        self.assertIn("config/MILL-SCRIPT-INVENTORY.json", tracked)

    def test_non_repository_cannot_be_reported_as_clean_scope(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(msi.MillScriptInventoryError):
                msi.tracked_paths(Path(temp))

    def test_invalid_qlty_exclusion_configuration_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".qlty").mkdir()
            for value in ('"not an array"', '[42]'):
                with self.subTest(value=value):
                    (root / ".qlty/qlty.toml").write_text(f"exclude_patterns = {value}\n")
                    with self.assertRaises(msi.MillScriptInventoryError):
                        msi.qlty_exclude_patterns(root)

    def test_explicit_inventory_cannot_bypass_shape_checks(self):
        for field, value in (("scripts", None), ("match_patterns", None), ("quality_policy", None)):
            with self.subTest(field=field):
                document = dict(msi.INVENTORY)
                document[field] = value
                with self.assertRaises(msi.MillScriptInventoryError):
                    msi.check_inventory(inventory=document, tracked=())

    def test_check_mode_refuses_reported_defects_but_report_mode_exposes_them(self):
        report = {"ok": False, "unclassified": ["pipelines/new_mill.py"]}
        for arguments, expected in ((["--check"], 1), ([], 0)):
            with self.subTest(arguments=arguments), patch.object(msi, "check_inventory", return_value=report):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    self.assertEqual(msi.main(arguments), expected)
                self.assertEqual(json.loads(output.getvalue()), report)

    def test_experiment_imports_are_refused_even_without_a_listed_stem(self):
        self.assertEqual(msi.archived_import_hits("import experiments.unknown", ()), ("experiments",))
