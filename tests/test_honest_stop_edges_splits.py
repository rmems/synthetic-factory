"""Error branches for the honest-stop family registration."""

import importlib
import sys
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(PIPELINES))

PRODUCED_AT = "2026-10-20T23:00:00Z"

import pipelines.honest_stop as honest_stop_package

import honest_stop.vocabulary as cv
from honest_stop import splits
from honest_stop.splits import config_digest, load_family


def _family():
    return load_family()


class SplitTests(unittest.TestCase):
    def test_config_helpers_reject_bad_documents(self):
        self.assertTrue(_family().config_sha256.startswith("sha256:"))
        missing = Path("/no/such/honest-stop-family.json")
        with self.assertRaises(cv.FamilyError) as caught:
            splits._read_bytes(missing)
        self.assertEqual(caught.exception.code, "config.unreadable")
        with self.assertRaises(cv.FamilyError) as caught:
            splits._decode(Path("x.json"), b"{")
        self.assertEqual(caught.exception.code, "config.json")
        with mock.patch("honest_stop.splits.load_strict_json", side_effect=RecursionError):
            with self.assertRaises(cv.FamilyError) as caught:
                splits._decode(Path("x.json"), b"{}")
            self.assertEqual(caught.exception.code, "config.json")
        with self.assertRaises(cv.FamilyError) as caught:
            splits._as_object(Path("x.json"), [])
        self.assertEqual(caught.exception.code, "config.json")
        with self.assertRaises(cv.FamilyError) as caught:
            splits._require_keys({"a": 1}, ("a", "b"), "config.keys")
        self.assertEqual(caught.exception.code, "config.keys")
        with self.assertRaises(cv.FamilyError) as caught:
            splits._pin_matches({}, "family", cv.FAMILY)
        self.assertEqual(caught.exception.code, "config.pin")
        with self.assertRaises(cv.FamilyError) as caught:
            splits._pins({})
        self.assertEqual(caught.exception.code, "config.pin")
        with mock.patch.object(splits.Path, "is_file", return_value=False):
            with self.assertRaises(cv.FamilyError) as caught:
                splits._require_schema_file()
            self.assertEqual(caught.exception.code, "config.schema")

    def test_split_and_exclusion_helpers_reject_bad_rows(self):
        self.assertIn("underspecified-request", _family().splits)
        with self.assertRaises(cv.FamilyError) as caught:
            splits._require_mapping([])
        self.assertEqual(caught.exception.code, "config.splits")
        with self.assertRaises(cv.FamilyError) as caught:
            splits._require_scenario_keys({}, {"missing-credential"})
        self.assertEqual(caught.exception.code, "config.splits")
        self.assertFalse(splits._known_split(1))
        self.assertFalse(splits._known_split("nope"))
        self.assertTrue(splits._known_split("train"))
        with self.assertRaises(cv.FamilyError) as caught:
            splits._require_known_split("missing-credential", "nope")
        self.assertEqual(caught.exception.code, "config.splits")
        collected = splits._collect_splits({"missing-credential": "train"})
        self.assertEqual(collected, {"missing-credential": "train"})
        with self.assertRaises(cv.FamilyError) as caught:
            splits._as_list("id")
        self.assertEqual(caught.exception.code, "config.exclusion")
        with self.assertRaises(cv.FamilyError) as caught:
            splits._nonempty([])
        self.assertEqual(caught.exception.code, "config.exclusion")
        self.assertFalse(splits._text_item(1))
        self.assertFalse(splits._text_item("  "))
        self.assertTrue(splits._text_item("task"))
        with self.assertRaises(cv.FamilyError) as caught:
            splits._all_text([1])
        self.assertEqual(caught.exception.code, "config.exclusion")
        self.assertFalse(splits._unique(["a", "a"]))
        self.assertTrue(splits._unique(["a"]))
        self.assertFalse(splits._sorted_rows(["b", "a"]))
        self.assertTrue(splits._sorted_rows(["a", "b"]))
        self.assertFalse(splits._unique_sorted(["b", "a"]))
        self.assertTrue(splits._unique_sorted(["a"]))
        with self.assertRaises(cv.FamilyError) as caught:
            splits._require_unique_sorted(["a", "a"])
        self.assertEqual(caught.exception.code, "config.exclusion")
        with self.assertRaises(cv.FamilyError) as caught:
            splits._task_ids(["b", "a"])
        self.assertEqual(caught.exception.code, "config.exclusion")

    def test_exclusion_document_must_match_the_held_out_list(self):
        bad_version = {
            "schema_version": "nope",
            "list": cv.EXCLUSION_LIST,
            "note": "kept",
            "task_ids": ["honest-stop-underspecified-request"],
        }
        self.assertFalse(splits._version_ok(bad_version))
        bad_list = dict(bad_version, schema_version=cv.EXCLUSION_SCHEMA, list="other")
        self.assertFalse(splits._version_ok(bad_list))
        self.assertTrue(splits._version_ok(dict(bad_list, list=cv.EXCLUSION_LIST)))
        with self.assertRaises(cv.FamilyError) as caught:
            splits._require_version(bad_version)
        self.assertEqual(caught.exception.code, "config.exclusion")
        self.assertFalse(splits._note_ok(1))
        self.assertFalse(splits._note_ok("  "))
        self.assertTrue(splits._note_ok("kept"))
        with self.assertRaises(cv.FamilyError) as caught:
            splits._require_note({"note": "  "})
        self.assertEqual(caught.exception.code, "config.exclusion")
        with self.assertRaises(cv.FamilyError) as caught:
            splits._exclusion(bad_version)
        self.assertEqual(caught.exception.code, "config.exclusion")
        family = _family()
        with self.assertRaises(cv.FamilyError) as caught:
            splits._held_out_agrees(family.splits, frozenset())
        self.assertEqual(caught.exception.code, "config.exclusion")
        self.assertEqual(config_digest(), family.config_sha256)

    def test_package_form_executes_the_sibling_preamble(self):
        self.assertEqual(_family().dataset, cv.DATASET)
        direct = sys.modules.pop("honest_stop._contract", None)
        packaged = sys.modules.pop("pipelines.honest_stop._contract", None)
        try:
            loaded = importlib.import_module("pipelines.honest_stop._contract")
            self.assertTrue(callable(loaded.load_strict_json))
        finally:
            if direct is not None:
                sys.modules["honest_stop._contract"] = direct
                sys.modules["pipelines.honest_stop._contract"] = direct
                honest_stop_package._contract = direct
            elif packaged is not None:
                sys.modules["pipelines.honest_stop._contract"] = packaged
