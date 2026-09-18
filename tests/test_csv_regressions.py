"""CSV mill regressions: import safety, catalog identity and JSON refusals."""

from __future__ import annotations

import contextlib
import io
from itertools import product
import json
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import tempfile
import unittest

from pipelines.csv_mill import catalog, cli, generate
from pipelines.csv_mill._contract import CsvRefusal
from tests import csv_import_probe
from tests.test_csv import COMMITTED, TINY_PAIR, _dict_source


class CsvRegressions(unittest.TestCase):
    def test_both_import_orders_preserve_stdlib_and_bind_every_sibling(self):
        for first, preload in product(("csv_mill", "pipelines.csv_mill"), (False, True)):
            with (
                self.subTest(first=first, preload=preload),
                ProcessPoolExecutor(
                    max_workers=1, mp_context=multiprocessing.get_context("spawn")
                ) as pool,
            ):
                report = pool.submit(csv_import_probe.probe, first, preload).result(timeout=120)
                self.assertEqual(report["rows"], [["a", "b"]])
                self.assertEqual(report["split_modules"], [])
                self.assertTrue(report["same_package"])
                self.assertTrue(report["same_stdlib"])
                self.assertEqual(report["exports"], sorted(csv_import_probe.MODULES))

    def test_repeated_source_keyword_is_refused(self):
        source = _dict_source([TINY_PAIR]).replace("dict(slug=", "dict(slug='discarded', slug=", 1)
        with self.assertRaises(CsvRefusal) as caught:
            catalog.plants_from_source(source, mill_id="csv_r114", source="bad.py")
        self.assertEqual(caught.exception.code, "SOURCE_NOT_PARSEABLE")

    def test_selected_plant_and_all_keep_the_same_round_and_identity(self):
        loaded = catalog.load_catalog(COMMITTED)
        last = loaded.plants[-1]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name, selection in (
                ("one", {"plant_id": last.plant_id}),
                ("all", {"all_plants": True}),
            ):
                generate.run(generate.GenerateRequest(COMMITTED, root / name, **selection))
            one = [
                json.loads(line) for line in (root / "one/records.jsonl").read_text().splitlines()
            ]
            all_rows = [
                json.loads(line) for line in (root / "all/records.jsonl").read_text().splitlines()
            ]
        self.assertEqual(one, all_rows[-2:])
        self.assertEqual(one[0]["meta"]["round"], 129)

    def test_colliding_success_and_failure_ids_leave_no_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "catalog"
            source.mkdir()
            rows = [
                json.loads(line) for line in (COMMITTED / "plants.jsonl").read_text().splitlines()
            ]
            rows[0]["fail"] = rows[0]["slug"]
            payload = "".join(json.dumps(row) + "\n" for row in rows)
            (source / "plants.jsonl").write_text(payload, encoding="utf-8")
            meta = json.loads((COMMITTED / "CATALOG.json").read_text())
            meta["plants_sha256"] = catalog.sha256_bytes(payload.encode())
            (source / "CATALOG.json").write_text(json.dumps(meta), encoding="utf-8")
            destination = root / "output"
            with self.assertRaises(CsvRefusal):
                generate.run(generate.GenerateRequest(source, destination, all_plants=True))
            self.assertFalse(destination.exists())

    def test_parser_failures_in_json_mode_are_structured(self):
        for argv in (
            ["generate", "--all", "--json"],
            ["generate", "--out", "unused", "--round", "bad", "--json"],
            ["catalog-check", "--unknown", "--json"],
        ):
            with self.subTest(argv=argv):
                out, err = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    code = cli.run(argv)
                self.assertEqual(code, 2)
                self.assertEqual(err.getvalue(), "")
                self.assertEqual(json.loads(out.getvalue())["code"], "USAGE")


if __name__ == "__main__":
    unittest.main()
