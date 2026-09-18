"""Catalog and CLI refusals do not depend on host integer or filename codecs."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

from pipelines.csv_mill import catalog
from pipelines.csv_mill._contract import FACTORY, RECORD_PREFIX, load_strict_json
from tests.test_csv import FIRST_PLANT, TINY_PAIR, _dict_source, invoke


class SerializationBoundaries(unittest.TestCase):
    def test_large_round_extraction_ignores_host_digit_cap(self):
        digits = "1" + "0" * 700
        source = _dict_source([TINY_PAIR], FAC=FACTORY, PREFIX=RECORD_PREFIX)
        source += "\nCATALOG_FIRST = " + hex(10**700) + "\n"
        original = sys.get_int_max_str_digits()
        try:
            sys.set_int_max_str_digits(640)
            rows = catalog.plants_from_source(source, mill_id="csv_r" + digits, source="literal.py")
            self.assertEqual(rows[0]["base_round"], 10**700)
        finally:
            sys.set_int_max_str_digits(original)

    def test_catalog_integer_decoder_ignores_host_digit_cap(self):
        original = sys.get_int_max_str_digits()
        try:
            sys.set_int_max_str_digits(640)
            self.assertEqual(load_strict_json('{"base_round":' + "1" + "0" * 700 + '}')["base_round"], 10**700)
        finally:
            sys.set_int_max_str_digits(original)

    def test_cli_round_and_emitted_ids_ignore_host_digit_cap(self):
        original = sys.get_int_max_str_digits()
        digits = "1" + "0" * 700
        try:
            sys.set_int_max_str_digits(640)
            with tempfile.TemporaryDirectory() as tmp:
                destination = Path(tmp) / "run"
                code, out, err = invoke([
                    "generate", "--plant", FIRST_PLANT, "--round", digits,
                    "--out", str(destination), "--json",
                ])
                self.assertEqual((code, err), (0, ""), out)
                self.assertIn("r" + digits, (destination / "records.jsonl").read_text())
                self.assertIn("r" + digits, (destination / "NOTES.md").read_text())
        finally:
            sys.set_int_max_str_digits(original)

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
