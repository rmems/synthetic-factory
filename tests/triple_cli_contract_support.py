"""Shared CLI contract of the two leftover3 triple families, ``code_leftover3`` and ``crp``.

Both ``cli.py`` files expose the same surface: ``catalog-check`` and
``generate --round N --out DIR``, exit 2 with a coded refusal object for a
contract refusal and an ``"error"`` object for any other exception. A test
module mixes :class:`TripleCliContractMixin` into a ``unittest.TestCase`` and
sets ``spec`` to its CLI. The mixin is not a ``TestCase`` itself, so it never
runs unbound.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from types import ModuleType
from typing import ClassVar

from mill_cli_entry_support import (
    assert_usage_error,
    main_in_process,
    module_entry,
    scratch_dir,
)

CHECK = "catalog-check"
GENERATE = "generate"
JSON = "--json"
OUT = "--out"
ROUND = "--round"
OUT_OF_DOMAIN = "ROUND_OUT_OF_DOMAIN"


@dataclass(frozen=True)
class TripleCli:
    """One triple CLI under test."""

    cli: ModuleType
    module_name: str  # what ``python3 -m`` runs
    valid_round: str  # a round inside the catalog window
    check_prose: str  # the ``catalog-check`` line, newline included


class TripleCliContractMixin:
    """Behaviour both triple CLIs share, for the CLI that ``spec`` names.

    Mix it in before ``unittest.TestCase``: ``class X(TripleCliContractMixin, TestCase)``.
    """

    spec: ClassVar[TripleCli]

    def setUp(self):
        self.scratch = scratch_dir(self)
        self.dest = self.scratch / "out"

    def generate(self, round_n: str, out: str, *extra: str):
        return main_in_process(self.spec.cli.run, [GENERATE, ROUND, round_n, OUT, out, *extra])

    def blocked_out(self) -> str:
        """An ``--out`` whose parent is a regular file, so creating it raises an OSError."""
        blocker = self.scratch / "blocker"
        blocker.write_text("not a directory\n", encoding="utf-8")
        return str(blocker / "out")

    def test_catalog_check_prose_counts_plants_triples_and_rounds(self):
        result = main_in_process(self.spec.cli.run, [CHECK])
        self.assertEqual(result, (0, self.spec.check_prose, ""))

    def test_python_m_runs_the_same_catalog_check(self):
        result = main_in_process(module_entry(self.spec.module_name), [CHECK])
        self.assertEqual(result, (0, self.spec.check_prose, ""))

    def test_an_out_of_domain_round_is_refused_as_json_without_a_destination(self):
        result = self.generate("1", str(self.dest), JSON)
        payload = json.loads(result.stdout)
        self.assertEqual((result.returncode, payload["code"]), (2, OUT_OF_DOMAIN))
        self.assertEqual((payload["command"], payload["status"]), (GENERATE, "refused"))
        self.assertFalse(self.dest.exists())

    def test_an_out_of_domain_round_is_refused_on_stderr(self):
        result = self.generate("1", str(self.dest))
        self.assertEqual((result.returncode, result.stdout), (2, ""))
        self.assertTrue(result.stderr.startswith(f"{OUT_OF_DOMAIN}: "))

    def test_an_existing_destination_is_refused_on_stderr(self):
        self.dest.mkdir()
        result = self.generate(self.spec.valid_round, str(self.dest))
        self.assertEqual(result, (2, "", f"DESTINATION_EXISTS: {self.dest} already exists\n"))

    def test_an_os_error_while_writing_is_reported_as_an_error_object(self):
        result = self.generate(self.spec.valid_round, self.blocked_out(), JSON)
        payload = json.loads(result.stdout)
        self.assertEqual((result.returncode, payload["command"]), (2, GENERATE))
        self.assertEqual(payload["status"], "error")
        self.assertIn("FileExistsError", payload["message"])

    def test_an_os_error_while_writing_is_reported_on_stderr(self):
        result = self.generate(self.spec.valid_round, self.blocked_out())
        self.assertEqual((result.returncode, result.stdout), (2, ""))
        self.assertIn("FileExistsError", result.stderr)

    def test_an_unknown_command_is_rejected(self):
        assert_usage_error(self, self.spec.cli.run, ["catalog"], "invalid choice: 'catalog'")

    def test_generate_requires_a_round(self):
        fragment = "the following arguments are required: --round"
        assert_usage_error(self, self.spec.cli.run, [GENERATE, OUT, "unused"], fragment)

