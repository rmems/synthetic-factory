#!/usr/bin/env python3
"""Exact JSON numeric parsing and serialization regressions."""

from __future__ import annotations

import copy
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from fractions import Fraction
from pathlib import Path

PIPELINES = Path(__file__).resolve().parents[1] / "pipelines"
sys.path.insert(0, str(PIPELINES))

from exact_json import (  # noqa: E402
    ExactJSONFloat,
    dumps_exact_json,
    exact_fraction,
    exact_json_integer,
    json_number_from_fraction,
    parse_finite_json_float,
)
import spike_probe  # noqa: E402

FIXTURE = PIPELINES.parent / "tests" / "fixtures" / "bridge_gate_snn.jsonl"


class ExactJSONNumbers(unittest.TestCase):
    def test_parse_serialize_parse_preserves_decimal_token(self):
        payload = '{"rate":25.000000000000001,"label":"25.000000000000001"}'
        parsed = json.loads(payload, parse_float=parse_finite_json_float)

        self.assertIsInstance(parsed["rate"], float)
        self.assertIsInstance(parsed["rate"], ExactJSONFloat)
        self.assertEqual(
            exact_fraction(parsed["rate"]),
            Fraction("25.000000000000001"),
        )
        encoded = dumps_exact_json(parsed)
        self.assertEqual(
            encoded,
            '{"label":"25.000000000000001","rate":25.000000000000001}',
        )
        reparsed = json.loads(encoded, parse_float=parse_finite_json_float)
        self.assertEqual(exact_fraction(reparsed["rate"]), exact_fraction(parsed["rate"]))

    def test_integrality_uses_the_exact_token(self):
        self.assertEqual(exact_json_integer(parse_finite_json_float("2.56e2")), 256)
        self.assertIsNone(exact_json_integer(parse_finite_json_float("1.00000000000000001")))

    def test_fraction_derivation_stays_json_exact(self):
        derived = json_number_from_fraction(Fraction(1, 40))

        self.assertEqual(dumps_exact_json({"window": derived}), '{"window":0.025}')

    def test_overflowing_float_token_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "non-finite JSON number"):
            parse_finite_json_float("1e999")

    def test_exact_decimal_expansion_is_bounded_before_fraction_construction(self):
        self.assertEqual(float(parse_finite_json_float("1e308")), 1e308)
        self.assertEqual(exact_fraction(parse_finite_json_float("1e-00000")), 1)
        hostile_tokens = (
            "1e-4097",
            "1e-10000",
            "0." + ("1" * 4097),
        )
        for token in hostile_tokens:
            with self.subTest(token=token[:32]), self.assertRaisesRegex(
                ValueError, "exact-decimal limit"
            ):
                parse_finite_json_float(token)

        with self.assertRaisesRegex(ValueError, "exact-decimal limit"):
            json_number_from_fraction(Fraction(1, 10**4097))

    def test_exact_float_is_immutable_across_copy_operations(self):
        value = parse_finite_json_float("25.000000000000001")

        self.assertIs(copy.copy(value), value)
        self.assertIs(copy.deepcopy(value), value)

    def test_scalar_serialization_matches_json_contract(self):
        payload = {
            "none": None,
            "true": True,
            "false": False,
            "integer": -7,
            "float": -0.0,
            "exact": parse_finite_json_float("1.00000000000000001"),
            "unicode": "café",
        }

        encoded = dumps_exact_json(payload, ensure_ascii=False)
        self.assertIn('"exact":1.00000000000000001', encoded)
        self.assertIn('"unicode":"café"', encoded)
        self.assertIn('"float":-0.0', encoded)
        self.assertIn('"true":true', encoded)
        self.assertIn('"false":false', encoded)
        self.assertIn('"none":null', encoded)
        self.assertIn(
            '"unicode":"caf\\u00e9"',
            dumps_exact_json(payload, ensure_ascii=True),
        )
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                dumps_exact_json(value)
        with self.assertRaises(TypeError):
            dumps_exact_json(object())

    def test_probe_jsonl_preserves_a_contractual_decimal_token(self):
        neurons = 10**18 + 2
        spikes = round(Fraction("25.000000000000001") * Fraction("0.04") * neurons)
        record = json.loads(FIXTURE.read_text(encoding="utf-8").splitlines()[0])
        record["raster"].update(
            {"neurons": neurons, "mean_rate_hz": 25, "spikes": spikes}
        )
        record["raster"].pop("energy_pJ", None)
        record["raster"].pop("energy_uJ", None)
        payload = json.dumps(record, separators=(",", ":")).replace(
            '"mean_rate_hz":25',
            '"mean_rate_hz":25.000000000000001',
            1,
        )
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "exact.jsonl"
            source.write_text(payload + "\n", encoding="utf-8")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = spike_probe.main(["--jsonl", str(source)])

        self.assertEqual(exit_code, 0)
        self.assertIn('"mean_rate_hz":25.000000000000001', stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
