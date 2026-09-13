#!/usr/bin/env python3
"""Contracts for the split compose-run CLI and facade adapters."""

from __future__ import annotations

import io
import importlib
import json
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

if __package__:
    from .compose_curated_import_contract_support import clean_process_identity_exit_code
else:
    from compose_curated_import_contract_support import clean_process_identity_exit_code


REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

compose_curated_run = importlib.import_module("compose_curated_run")
compose_curated_run_cli = importlib.import_module("compose_curated_run_cli")


class ComposeRunAdapterContracts(unittest.TestCase):
    def test_run_adapters_and_bootstrap_have_one_package_direct_identity(self):
        for package_first in (False, True):
            with self.subTest(package_first=package_first):
                exit_code = clean_process_identity_exit_code(
                    REPO,
                    (
                        "compose_curated_run_bootstrap",
                        "compose_curated_run_cli",
                        "compose_curated_run_facade",
                    ),
                    package_first=package_first,
                )
                self.assertEqual(exit_code, 0)

    def test_cli_strict_failure_prints_summary_then_blockers_in_order(self):
        summary = {
            "audit": {
                "training_ready": False,
                "blockers": ["first_blocker", "second_blocker"],
            }
        }
        services = SimpleNamespace(run=object(), caught_errors=(ValueError,))
        stdout = io.StringIO()
        stderr = io.StringIO()

        with (
            mock.patch.object(compose_curated_run_cli, "compose_run", return_value=summary),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            status = compose_curated_run_cli.main(["--strict", "source", "destination"], services)

        self.assertEqual(status, 1)
        self.assertEqual(json.loads(stdout.getvalue()), summary)
        self.assertEqual(
            stderr.getvalue().splitlines(),
            ["blocker: first_blocker", "blocker: second_blocker"],
        )

    def test_cli_caught_error_is_reported_without_a_partial_summary(self):
        services = SimpleNamespace(run=object(), caught_errors=(ValueError,))
        stdout = io.StringIO()
        stderr = io.StringIO()

        with (
            mock.patch.object(
                compose_curated_run_cli,
                "compose_run",
                side_effect=ValueError("invalid run coordinate"),
            ),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            status = compose_curated_run_cli.main(["source", "destination"], services)

        self.assertEqual(status, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(
            stderr.getvalue(),
            "compose_curated: invalid run coordinate\n",
        )

    def test_cli_forwards_immutable_coordinates_and_optional_hooks(self):
        summary = {"audit": {"training_ready": True, "blockers": []}}
        services = SimpleNamespace(run=object(), caught_errors=(ValueError,))
        hooks = object()

        with (
            mock.patch.object(
                compose_curated_run_cli,
                "compose_run",
                return_value=summary,
            ) as run,
            redirect_stdout(io.StringIO()),
        ):
            status = compose_curated_run_cli.main(
                ["--units-migration", "units.json", "source", "destination"],
                services,
                hooks,
            )

        self.assertEqual(status, 0)
        context, passed_services, passed_hooks = run.call_args.args
        self.assertEqual(context.source_run, Path("source"))
        self.assertEqual(context.destination, Path("destination"))
        self.assertEqual(context.units_migration, Path("units.json"))
        self.assertIs(passed_services, services.run)
        self.assertIs(passed_hooks, hooks)

    def test_invalid_factory_roots_are_refused_before_coordinate_publication(self):
        for factory in (".", "..", "/factory", "factory/nested"):
            with self.subTest(factory=factory):
                with self.assertRaisesRegex(
                    compose_curated_run.ComposeError,
                    "invalid factory identity for published source coordinate",
                ):
                    compose_curated_run._published_source_coordinate("batch-r01.jsonl", factory)


if __name__ == "__main__":
    unittest.main()
