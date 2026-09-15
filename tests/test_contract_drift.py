#!/usr/bin/env python3
"""ACM contract-drift skeleton: identity, AST extract, committed catalog."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from contract_drift import catalog  # noqa: E402
from contract_drift import catalog_extract  # noqa: E402
from contract_drift import check  # noqa: E402
from contract_drift import identity  # noqa: E402

FIXTURE = REPO / "tests" / "fixtures" / "contract-drift" / "tiny-source"


class Identity(unittest.TestCase):
    def test_family_maps_to_the_registered_factory(self):
        self.assertEqual(identity.FAMILY, "acm")
        self.assertEqual(identity.FACTORY_NAME, "api-contract-migration-factory")
        self.assertEqual(identity.GENERATOR, "grok-4.6")
        self.assertEqual(identity.QUOTA, 2)
        self.assertEqual(identity.STEPS, 16)
        self.assertEqual(identity.ID_PREFIX, "acm")
        self.assertEqual(identity.SOURCE_COMMIT, "6d5ed0c1cac87618a05fab37f2e59bebca0a6031")

    def test_refuse_vendor_paths_fails_closed_on_mill_scripts(self):
        with self.assertRaises(SystemExit) as caught:
            identity.refuse_vendor_paths((Path("experiments") / "acm-mill-r3561.py",))
        self.assertIn("acm-mill-r3561.py", str(caught.exception))


class Extract(unittest.TestCase):
    def test_ast_extract_reads_pairs_and_plant_gen_without_exec(self):
        payload = catalog_extract.extract_tree(FIXTURE)
        check.check_catalog(payload)
        slugs = {(row["success_slug"], row["fail_slug"]) for row in payload["rows"]}
        self.assertEqual(
            slugs,
            {
                ("oas-info-title", "leftover-missing-title"),
                ("oas-type-boolean", "leftover-truthy-string"),
                ("oas-host-required", "leftover-missing-host"),
            },
        )
        title = next(row for row in payload["rows"] if row["success_slug"] == "oas-info-title")
        self.assertEqual(title["catalog_id"], "r1")
        self.assertEqual(title["kind"], "mill-pairs")
        self.assertEqual(title["field"], "title")
        self.assertEqual(title["fetch1"], "https://spec.example/oas#info")
        boolean = next(row for row in payload["rows"] if row["success_slug"] == "oas-type-boolean")
        self.assertEqual(boolean["catalog_id"], "r2")
        self.assertEqual(boolean["kind"], "plant-gen")
        host = next(row for row in payload["rows"] if row["success_slug"] == "oas-host-required")
        self.assertEqual(host["catalog_id"], "r3")
        self.assertEqual(host["fetch1"], "https://spec.example/oas#host")
        kinds = {item["kind"]: item for item in payload["sources"]}
        self.assertNotIn("loop", kinds)
        self.assertEqual(kinds["mill"]["path"], "acm-pairs-r1.py")
        self.assertEqual(kinds["mill"]["loop_mills"], [])
        self.assertEqual(payload["extract"]["method"], "ast.parse")
        self.assertFalse(payload["extract"]["exec"])
        self.assertIn("w131", payload["bans"]["slug_needles"])
        self.assertIn("thought", payload["bans"]["blob_keys"])

    def test_loop_mill_names_are_extracted_from_a_temp_tree(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "acm-loop-r1.py").write_text(
                'LEGACY_MILL = "acm-mill-r1.py"\n',
                encoding="utf-8",
            )
            payload = catalog_extract.extract_tree(root)
        kinds = {item["kind"]: item for item in payload["sources"]}
        self.assertEqual(kinds["loop"]["loop_mills"], ["acm-mill-r1.py"])
        self.assertEqual(payload["row_count"], 0)

    def test_write_refuses_an_existing_destination_and_vendor_names(self):
        payload = catalog_extract.extract_tree(FIXTURE)
        with tempfile.TemporaryDirectory() as raw:
            dest = Path(raw) / "catalog"
            dest.mkdir()
            catalog.write_catalog(dest, payload)
            self.assertTrue((dest / catalog.CATALOG_FILENAME).is_file())
            self.assertTrue((dest / catalog.ROWS_FILENAME).is_file())
            loaded = catalog.load_catalog(dest)
            self.assertEqual(loaded["row_count"], 3)
            again = Path(raw) / "catalog"
            with self.assertRaises(FileExistsError):
                again.mkdir(exist_ok=False)
            with self.assertRaises(SystemExit):
                identity.refuse_vendor_paths((dest / "acm-mill-r1.py",))


class CommittedCatalog(unittest.TestCase):
    def test_committed_catalog_loads_and_passes_shape_checks(self):
        payload = catalog.load_catalog()
        check.check_catalog(payload)
        self.assertGreater(payload["row_count"], 0)
        self.assertEqual(payload["row_count"], len(payload["rows"]))
        self.assertEqual(payload["extract"]["source_commit"], identity.SOURCE_COMMIT)
        self.assertFalse(payload["extract"]["exec"])
        loops = [item for item in payload["sources"] if item["kind"] == "loop"]
        self.assertGreater(len(loops), 0)
        self.assertTrue(any(item["loop_mills"] for item in loops))

    def test_repository_does_not_vendor_acm_mill_scripts(self):
        check.check_tree_has_no_vendor(REPO)
        package = REPO / "pipelines" / "contract_drift"
        check.check_tree_has_no_vendor(package)
        catalogs = REPO / "catalogs" / identity.CATALOG_ID
        check.check_tree_has_no_vendor(catalogs)
        self.assertEqual(list((REPO / "tests").rglob("acm-loop-*.py")), [])
        self.assertFalse((FIXTURE / "acm-loop-r1.py").exists())


if __name__ == "__main__":
    unittest.main()
