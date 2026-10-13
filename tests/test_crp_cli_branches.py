"""crp CLI: catalog-check waves and generate refusals and errors, driven in process."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
for _path in (TESTS, TESTS.parent / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import triple_cli_contract_support as contract
from crp import cli as crp_cli
from mill_cli_entry_support import assert_usage_error, main_in_process


class CrpCliContractTests(contract.TripleCliContractMixin, unittest.TestCase):
    # An out-of-domain round is pinned by its code only: the message names the
    # leftover3 window although generate accepts every wave (owner finding).
    spec = contract.TripleCli(
        cli=crp_cli,
        module_name="crp.cli",
        valid_round="729",
        check_prose="catalog-check ok: 48 plants (16 triples, 48 nouns) r729-r744\n",
    )

    def test_catalog_check_json_pins_the_default_leftover3_report(self):
        payload = json.loads(main_in_process(crp_cli.run, [contract.CHECK, contract.JSON]).stdout)
        expected = {
            "catalog_id": "crp-leftover3-v1",
            "command": contract.CHECK,
            "first_round": 729,
            "last_round": 744,
            "nouns": 48,
            "plants": 48,
            "status": "ok",
            "triples": 16,
        }
        self.assertEqual(payload, expected)

    def test_an_unknown_wave_is_rejected(self):
        argv = [contract.CHECK, "--wave", "r1"]
        assert_usage_error(self, crp_cli.run, argv, "invalid choice: 'r1'")


if __name__ == "__main__":
    unittest.main()
