"""PBC read-only CLI and the fail-closed plan / catalog refusals.

Each refusal case mutates one field of a committed plan or catalog copy and
asserts the exact ``PlanValidationError`` message, so the check order of the
loaders stays pinned.
"""

from __future__ import annotations

import contextlib
import copy
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from pbc import _contract, catalog, cli

PLAN_PATH = REPO / _contract.DEFAULT_PLAN_PATH


def _run_cli(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


class PbcCliTests(unittest.TestCase):
    def test_plan_text_summarises_the_committed_slice(self):
        code, out, _ = _run_cli(["plan"])
        plan = catalog.load_mill_usage_burst_plan()
        counts = plan.counts()
        self.assertEqual(code, 0)
        self.assertEqual(
            out.strip(),
            f"slice {plan.slice} {plan.label}: {counts['mills']} mills, "
            f"{counts['rounds']} committed rounds, {counts['episodes']} episodes",
        )

    def test_plan_json_lists_every_mill_in_plan_order(self):
        code, out, _ = _run_cli(["plan", "--json"])
        payload = json.loads(out)
        plan = catalog.load_mill_usage_burst_plan()
        self.assertEqual(code, 0)
        self.assertEqual(payload["factory"], _contract.FACTORY)
        self.assertEqual(payload["counts"], plan.counts())
        self.assertEqual([row["id"] for row in payload["mills"]], [m.mill_id for m in plan.mills])
        first = payload["mills"][0]
        self.assertEqual(first["end_round"], plan.mills[0].end_round_inclusive)

    def test_plan_refusal_is_reported_on_stderr_with_exit_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "plan.json"
            raw = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
            raw["factory"] = "elsewhere"
            bad.write_text(json.dumps(raw), encoding="utf-8")
            code, out, err = _run_cli(["plan", "--plan", str(bad)])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertEqual(err.strip(), f"factory must be {_contract.FACTORY!r}")

    def test_catalog_prints_pins(self):
        code, out, _ = _run_cli(["catalog"])
        payload = json.loads(out)
        loaded = catalog.load_catalog()
        self.assertEqual(code, 0)
        self.assertEqual(payload["catalog_id"], loaded.catalog_id)
        self.assertEqual(payload["row_count"], len(loaded.pairs))
        self.assertEqual(payload["plants_sha256"], loaded.plants_sha256)
        self.assertEqual(payload["mills"], [mill.mill_id for mill in loaded.mills])

    def test_catalog_refusal_exits_2(self):
        boom = catalog.PlanValidationError("catalog drifted")
        with mock.patch.object(catalog, "load_catalog", side_effect=boom):
            code, out, err = _run_cli(["catalog"])
        self.assertEqual((code, out, err.strip()), (2, "", "catalog drifted"))


class PbcPlanRefusalTests(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def _refusal(self, raw, *, validate_plants=False) -> str:
        path = Path(self.tmp.name) / "plan.json"
        path.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaises(catalog.PlanValidationError) as caught:
            catalog.load_mill_usage_burst_plan(path, validate_plants=validate_plants)
        return str(caught.exception)

    def _mutated(self, edit):
        raw = copy.deepcopy(self.raw)
        edit(raw)
        return raw

    def test_identity_fields_are_checked_in_order(self):
        cases = {
            "schema_id": f"schema_id must be {_contract.PLAN_SCHEMA_ID!r}",
            "family_prefix": f"family_prefix must be {_contract.FAMILY!r}",
            "factory": f"factory must be {_contract.FACTORY!r}",
            "slice": f"slice must be {_contract.PLAN_SLICE!r}",
        }
        for field, message in cases.items():
            with self.subTest(field=field):
                raw = self._mutated(lambda r, f=field: r.__setitem__(f, "drift"))
                self.assertEqual(self._refusal(raw), message)

    def test_quota_must_be_the_pinned_integer(self):
        raw = self._mutated(lambda r: r.__setitem__("quota_per_round", True))
        self.assertEqual(self._refusal(raw), "quota_per_round must be an integer, got True")
        raw = self._mutated(lambda r: r.__setitem__("quota_per_round", _contract.QUOTA + 1))
        self.assertEqual(self._refusal(raw), f"quota_per_round must be {_contract.QUOTA}")

    def test_mill_entries_are_refused_field_by_field(self):
        cases = [
            (lambda r: r.__setitem__("mills", []), "mills must be a non-empty list"),
            (lambda r: r["mills"][0].__setitem__("id", ""), "mills[].id must be a non-empty string, got ''"),
            (
                lambda r: r["mills"][0].__setitem__("n_rounds", "3"),
                "mills[].n_rounds must be an integer, got '3'",
            ),
            (
                lambda r: r["mills"][0].__setitem__("pair_count", r["mills"][0]["n_rounds"] + 1),
                f"{self.raw['mills'][0]['id']}: pair_count must equal n_rounds",
            ),
            (
                lambda r: r["mills"][0].__setitem__("source", None),
                "mills[].source must be a non-empty string, got None",
            ),
        ]
        for edit, message in cases:
            with self.subTest(message=message):
                self.assertEqual(self._refusal(self._mutated(edit)), message)

    def test_deferred_mills_must_be_a_list_of_catalog_deferrals(self):
        cases = [
            (lambda r: r.__setitem__("deferred_mills", {}), "deferred_mills must be a list"),
            (
                lambda r: r["deferred_mills"].append({"id": "pbc_r1"}),
                "unexpected deferred mill 'pbc_r1'",
            ),
        ]
        for edit, message in cases:
            with self.subTest(message=message):
                self.assertEqual(self._refusal(self._mutated(edit)), message)

    def test_totals_drift_is_refused(self):
        totals = self.raw["totals"]
        cases = [
            ("mills", f"totals.mills is {totals['mills'] + 1!r}, expected {totals['mills']}"),
            ("deferred_mills", "totals.deferred_mills drifted"),
            ("full_pairs", "totals.full_pairs drifted from the full extract"),
            ("full_episodes", "totals.full_episodes drifted from the full extract"),
        ]
        for key, message in cases:
            with self.subTest(key=key):
                raw = self._mutated(lambda r, k=key: r["totals"].__setitem__(k, r["totals"][k] + 1))
                self.assertEqual(self._refusal(raw), message)

    def test_plan_counts_must_match_the_catalog(self):
        def swap(raw):
            raw["mills"][0], raw["mills"][1] = raw["mills"][1], raw["mills"][0]

        self.assertEqual(
            self._refusal(self._mutated(swap), validate_plants=True),
            "plan mill order drifted from committed CATALOG mills",
        )


class PbcCatalogRefusalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "pbc"
        self.root.mkdir()
        source = catalog.default_catalog_dir()
        for name in (catalog.CATALOG_FILENAME, catalog.PLANTS_FILENAME):
            shutil.copyfile(source / name, self.root / name)
        self.header = json.loads((self.root / catalog.CATALOG_FILENAME).read_text(encoding="utf-8"))

    def _refusal(self, header) -> str:
        (self.root / catalog.CATALOG_FILENAME).write_text(json.dumps(header), encoding="utf-8")
        with self.assertRaises(catalog.PlanValidationError) as caught:
            catalog.load_catalog(self.root)
        return str(caught.exception)

    def test_copied_catalog_loads(self):
        self.assertEqual(len(catalog.load_catalog(self.root).pairs), len(catalog.load_catalog().pairs))

    def test_mill_list_must_name_the_eight_burst_mills(self):
        header = copy.deepcopy(self.header)
        header["mills"] = header["mills"][:-1]
        self.assertEqual(self._refusal(header), "catalog mills must list the eight burst mills")

    def test_mill_rows_are_bound_to_their_first_pair(self):
        first = self.header["mills"][0]
        mill_id = first["mill_id"]
        cases = [
            ("first_ok_slug", "drift", f"{mill_id} first-pair slugs drifted"),
            ("full_n_rounds", first["full_n_rounds"] + 1, f"{mill_id} full_n_rounds drifted"),
            ("mill_id", "pbc_r1", "pbc_r1 has no committed pairs"),
        ]
        for key, value, message in cases:
            with self.subTest(key=key):
                header = copy.deepcopy(self.header)
                header["mills"][0][key] = value
                self.assertEqual(self._refusal(header), message)

    def test_a_deferred_mill_with_committed_pairs_is_refused(self):
        header = copy.deepcopy(self.header)
        mill_id = header["mills"][0]["mill_id"]
        header["mills"][0]["deferred"] = True
        self.assertEqual(self._refusal(header), f"{mill_id} is deferred but has committed pairs")

    def test_extract_deferred_mills_must_match(self):
        header = copy.deepcopy(self.header)
        header["extract"]["deferred_mills"] = ["pbc_r1"]
        self.assertEqual(self._refusal(header), "extract.deferred_mills drifted")


if __name__ == "__main__":
    unittest.main()
