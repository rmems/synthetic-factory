"""Fail-closed branches of the native compose run orchestration and its CLI."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
for _path in (TESTS, TESTS.parent / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import compose_curated
import compose_curated_run as run
import compose_mill
from compose_contract import ComposeError
from compose_curated_test_support import build_source_run
from compose_destination_branch_support import TempTreeCase

UNAUTHENTICATED = "oracle manifest does not authenticate the compose source snapshot"


def _cli_services() -> run.ComposeCliServices:
    return run.ComposeCliServices(
        run.facade_run_services(compose_curated, compose_mill.index_compose_mills),
        (ComposeError,),
    )


def _snapshot(relative: str, body: bytes):
    return types.SimpleNamespace(relative=relative, body=body)


class RunWiringTests(unittest.TestCase):
    def test_default_hooks_are_the_native_call_graph(self):
        hooks = run.default_run_hooks()

        self.assertIs(hooks.compose_one_line, run.compose_one_line)
        self.assertIs(hooks.capture_source_snapshot, run.capture_source_snapshot)
        self.assertIs(hooks.jsonl_physical_lines, run.jsonl_physical_lines)

    def test_facade_wiring_resolves_hooks_and_services(self):
        self.assertIsInstance(run.facade_run_hooks(compose_curated), run.ComposeRunHooks)
        self.assertIsInstance(
            run.facade_run_services(compose_curated, compose_mill.index_compose_mills),
            run.ComposeRunServices,
        )

    def test_cli_arguments_keep_their_defaults(self):
        args = run.parse_args(["source", "curated"])

        self.assertEqual(
            (args.source_run, args.destination, args.oracle_selection, args.units_migration),
            ("source", "curated", "all", None),
        )
        self.assertIs(args.strict, False)


class RunCliTests(TempTreeCase):
    def setUp(self) -> None:
        super().setUp()
        self.source = build_source_run(self.root / "source")
        self.destination = self.root / "curated"

    def run_main(self, *extra: str) -> tuple[int, str, str]:
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = run.main([str(self.source), str(self.destination), *extra], _cli_services())
        return code, stdout.getvalue(), stderr.getvalue()

    def test_existing_destination_exits_two_and_is_left_alone(self):
        self.destination.mkdir()
        (self.destination / "keep.txt").write_bytes(b"owner")

        code, _stdout, stderr = self.run_main()

        self.assertEqual(code, 2)
        self.assertEqual(
            stderr,
            f"compose_curated: refusing to overwrite an existing destination: {self.destination}\n",
        )
        self.assertEqual(sorted(path.name for path in self.destination.iterdir()), ["keep.txt"])

    def test_research_only_tree_composes_and_exits_zero(self):
        code, stdout, _stderr = self.run_main()

        self.assertEqual(code, 0)
        self.assertIs(json.loads(stdout)["audit"]["training_ready"], False)
        self.assertTrue((self.destination / "COMPOSE.json").is_file())

    def test_strict_mode_exits_one_and_lists_every_blocker(self):
        code, stdout, stderr = self.run_main("--strict")

        blockers = json.loads(stdout)["audit"]["blockers"]
        self.assertEqual(code, 1)
        self.assertEqual(stderr, "".join(f"blocker: {item}\n" for item in blockers))


class SnapshotCaptureTests(unittest.TestCase):
    @staticmethod
    def services(members, identities):
        return types.SimpleNamespace(
            source_jsonl_members=mock.Mock(side_effect=members),
            source_snapshot_identities=mock.Mock(side_effect=identities),
            captured_source_payloads=mock.Mock(return_value={"a.jsonl": b"{}\n"}),
        )

    def assert_capture_refused(self, message: str, services) -> None:
        with self.assertRaises(ComposeError) as caught:
            run.capture_source_snapshot(Path("run"), services)

        self.assertEqual(str(caught.exception), message)

    def test_member_set_drift_is_refused(self):
        identity = {"a.jsonl": ((1,), "f", True)}
        services = self.services([("a.jsonl",), ("a.jsonl", "b.jsonl")], [identity])

        self.assert_capture_refused(
            "source member set changed while capturing the source snapshot", services
        )

    def test_member_identity_drift_is_refused(self):
        before = {"a.jsonl": ((1,), "f", True)}
        after = {"a.jsonl": ((2,), "f", True)}
        services = self.services([("a.jsonl",), ("a.jsonl",)], [before, after])

        self.assert_capture_refused(
            "source member identity changed while capturing the source snapshot", services
        )


class OracleRouteTests(TempTreeCase):
    def write_manifest(self, payload: str) -> None:
        (self.root / "manifest.json").write_text(payload, encoding="utf-8")

    def assert_routes_refused(self, message: str) -> None:
        with self.assertRaises(ComposeError) as caught:
            run.authenticated_oracle_routes(self.root, {})

        self.assertEqual(str(caught.exception), message)

    def test_run_without_a_manifest_keeps_path_routing(self):
        self.assertEqual(run.authenticated_oracle_routes(self.root, {}), {})

    def test_other_manifest_schema_keeps_path_routing(self):
        self.write_manifest(json.dumps({"schema": "validate-run/v1"}))

        self.assertEqual(run.authenticated_oracle_routes(self.root, {}), {})

    def test_oracle_fields_under_another_schema_are_refused(self):
        self.write_manifest(json.dumps({"schema": "validate-run/v1", "oracle_commit": "abc"}))

        self.assert_routes_refused("oracle source manifest has an unsupported schema")

    def test_unreadable_manifest_is_refused(self):
        self.write_manifest("{")

        self.assert_routes_refused("source run manifest is unreadable")


class OracleSnapshotTests(unittest.TestCase):
    PAYLOADS = types.MappingProxyType({"oracle/a.jsonl": b"{}\n"})

    def assert_snapshot_refused(self, message: str, authentication) -> None:
        with self.assertRaises(ComposeError) as caught:
            run._require_oracle_snapshot(Path("run"), dict(self.PAYLOADS), authentication)

        self.assertEqual(str(caught.exception), message)

    def test_manifest_errors_are_refused(self):
        authentication = ({}, [_snapshot("oracle/a.jsonl", b"{}\n")], ["manifest error"])

        self.assert_snapshot_refused(UNAUTHENTICATED, authentication)

    def test_differing_captured_bytes_are_refused(self):
        authentication = ({}, [_snapshot("oracle/a.jsonl", b"[]\n")], [])

        self.assert_snapshot_refused(UNAUTHENTICATED, authentication)

    def test_failed_snapshot_validation_reports_its_first_error(self):
        authentication = ({}, [_snapshot("oracle/a.jsonl", b"{}\n")], [])
        validator = types.SimpleNamespace(
            validate_run_snapshot=mock.Mock(return_value=(None, ["first", "second"]))
        )

        # Seam: _oracle_validator is the only route to the sealed oracle validator.
        with (
            mock.patch.object(run, "_oracle_validator", return_value=validator),
            self.assertRaises(ComposeError) as caught,
        ):
            run._require_oracle_snapshot(Path("run"), dict(self.PAYLOADS), authentication)

        self.assertEqual(str(caught.exception), "oracle source snapshot failed validation: first")


if __name__ == "__main__":
    unittest.main()
