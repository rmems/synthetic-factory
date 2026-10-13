"""code_leftover3 CLI: catalog-check and generate refusals and errors, driven in process."""

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
from code_leftover3 import cli as code_cli
from mill_cli_entry_support import main_in_process, scratch_dir


class CodeLeftover3CliContractTests(contract.TripleCliContract):
    cli = code_cli
    # The flat spelling of ``python3 -m pipelines.code_leftover3.cli``: the same
    # ``__main__`` block, without re-importing the ``pipelines`` package.
    module_name = "code_leftover3.cli"
    valid_round = "679"
    check_prose = "catalog-check ok: 48 plants (16 triples, 48 nouns) r679-r694\n"


class CodeLeftover3CliReportTests(unittest.TestCase):
    def test_catalog_check_json_pins_the_whole_report(self):
        payload = json.loads(main_in_process(code_cli.run, [contract.CHECK, contract.JSON]).stdout)
        expected = {
            "catalog_id": "code-leftover3-prior-v1",
            "command": contract.CHECK,
            "first_round": 679,
            "last_round": 694,
            "nouns": 48,
            "plants": 48,
            "source_code_mill": "experiments/code_review_preference_mill_leftover3.py",
            "source_leftover3_mill": "experiments/crp-mill-leftover3.py",
            "status": "ok",
            "triples": 16,
        }
        self.assertEqual(payload, expected)

    def test_an_out_of_domain_round_names_the_catalog_window(self):
        dest = scratch_dir(self) / "out"
        argv = [contract.GENERATE, contract.ROUND, "695", contract.OUT, str(dest)]
        message = "ROUND_OUT_OF_DOMAIN: round must lie in [679, 694], got 695\n"
        self.assertEqual(main_in_process(code_cli.run, argv), (2, "", message))


if __name__ == "__main__":
    unittest.main()
