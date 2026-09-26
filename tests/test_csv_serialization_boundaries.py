"""Catalog and CLI refusals do not depend on host integer or filename codecs."""

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pipelines.csv_mill import catalog
from pipelines.csv_mill._contract import (
    FACTORY,
    RECORD_PREFIX,
    dumps_exact_json,
    load_strict_json,
)
from tests.test_csv import FIRST_PLANT, FIRST_SLUG, FIXTURE, TINY_PAIR, _dict_source, invoke


def _under_host_cap(digits, callback):
    original = sys.get_int_max_str_digits()
    try:
        sys.set_int_max_str_digits(digits)
        return callback()
    finally:
        sys.set_int_max_str_digits(original)


def _literal_pairs(**extra):
    return _dict_source([TINY_PAIR], FAC=FACTORY, PREFIX=RECORD_PREFIX, **extra)


class SerializationBoundaries(unittest.TestCase):
    def test_large_round_extraction_ignores_host_digit_cap(self):
        digits = "1" + "0" * 700
        source = _literal_pairs() + "\nCATALOG_FIRST = " + hex(10**700) + "\n"
        rows = _under_host_cap(640, lambda: catalog.plants_from_source(
            source, mill_id="csv_r" + digits, source="literal.py"
        ))
        self.assertEqual(rows[0]["base_round"], 10**700)

    def test_catalog_integer_decoder_ignores_host_digit_cap(self):
        payload = '{"base_round":' + "1" + "0" * 700 + "}"
        decoded = _under_host_cap(640, lambda: load_strict_json(payload))
        self.assertEqual(decoded["base_round"], 10**700)

    def test_cli_round_and_emitted_ids_ignore_host_digit_cap(self):
        digits = "1" + "0" * 700
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "run"

            def generate_large_round():
                return invoke([
                    "generate", "--plant", FIRST_PLANT, "--round", digits,
                    "--out", str(destination), "--json",
                ])

            code, out, err = _under_host_cap(640, generate_large_round)
            self.assertEqual((code, err), (0, ""), out)
            self.assertIn("r" + digits, (destination / "records.jsonl").read_text())
            self.assertIn("r" + digits, (destination / "NOTES.md").read_text())

    def test_surrogateescaped_destination_has_json_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "invalid-\udcff"
            code, out, err = invoke(
                ["generate", "--plant", FIRST_PLANT, "--out", str(destination), "--json"]
            )
            self.assertEqual(code, 2)
            self.assertEqual(err, "")
            self.assertIn("DESTINATION_INVALID", out)
            self.assertIsInstance(json.loads(out), dict)
            self.assertFalse(destination.exists())

    def test_suffix_fallback_ignores_host_digit_cap(self):
        digits = "1" + "0" * 700
        rows = _under_host_cap(640, lambda: catalog.plants_from_source(
            _literal_pairs(), mill_id="csv_r" + digits, source="literal.py"
        ))
        self.assertEqual(rows[0]["base_round"], 10**700)

    def test_round_allocation_ignores_host_digit_cap(self):
        base = 10 ** 700
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "catalog"
            _write_huge_round_catalog(directory, base)
            loaded = _under_host_cap(640, lambda: catalog.load_catalog(directory))
            self.assertEqual(loaded.plants[0].base_round, base)

    def test_resolved_undecodable_parent_is_json_safe_after_publish(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw_parent = os.path.join(os.fsencode(tmp), b"p-\xff")
            os.mkdir(raw_parent)
            alias = Path(tmp) / "alias"
            os.symlink(raw_parent, os.fsencode(alias))
            destination = alias / "run"
            code, out, err = invoke(
                ["generate", "--plant", f"csv_r0001:{FIRST_SLUG}",
                 "--catalog", str(FIXTURE), "--out", str(destination), "--json"]
            )
            self.assertEqual((code, err), (0, ""), out)
            payload = json.loads(out)
            published = payload["summary"]["published_destination"]
            published.encode("utf-8")
            self.assertNotIn("\udcff", published)
            self.assertTrue((destination / "records.jsonl").is_file())

    def test_is_under_raw_runtime_error_is_json_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "run"
            with patch(
                "pipelines.csv_mill._contract.is_under_raw",
                side_effect=RuntimeError("symlink loop"),
            ):
                code, out, err = invoke(
                    ["generate", "--plant", f"csv_r0001:{FIRST_SLUG}",
                     "--catalog", str(FIXTURE), "--out", str(destination), "--json"]
                )
            self.assertEqual((code, err), (2, ""))
            self.assertEqual(json.loads(out)["code"], "DESTINATION_INVALID")
            self.assertFalse(destination.exists())


def _write_huge_round_catalog(directory: Path, base: int) -> None:
    shutil.copytree(FIXTURE, directory)
    mill_id = "csv_r" + dumps_exact_json(base)
    row = json.loads((FIXTURE / "plants.jsonl").read_text().splitlines()[0])
    row.update(base_round=base, mill_id=mill_id, plant_id=f"{mill_id}:{row['slug']}")
    payload = dumps_exact_json(row, ensure_ascii=False, sort_keys=True) + "\n"
    (directory / "plants.jsonl").write_text(payload)
    meta = json.loads((FIXTURE / "CATALOG.json").read_text())
    meta["plants_sha256"] = catalog.sha256_bytes(payload.encode())
    meta["mills"][0].update(base_round=base, mill_id=mill_id)
    (directory / "CATALOG.json").write_text(
        dumps_exact_json(meta, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
