"""Explicit native replay authority is scoped to caller-selected executables."""

from pathlib import Path
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))
from oracle_grounded import admission, record


class NativeGateTests(unittest.TestCase):
    def item(self, profile="axon-stream-v1", family="spike-encoder-equivalence-pairs"):
        return {"family": family, "scenario": {"profile": profile},
                "oracle": {"implementation": "named-runtime"}}

    def test_plain_admission_never_spawns_a_runtime(self):
        with mock.patch.object(record, "reproduce") as replay:
            self.assertFalse(admission._measurement_eligibility(self.item())[0])
        replay.assert_not_called()

    def test_explicit_scope_replays_each_measurement_without_receipt_cache(self):
        from oracle_grounded import native_gate
        env = {"SF_ORACLE_RUST_BIN": "/explicit/runtime"}
        item = self.item()
        with mock.patch.object(native_gate, "runtime_environ", return_value=env):
            with mock.patch.object(record, "reproduce", return_value=("reproduced", "digest")) as replay:
                with native_gate.runtime_gate("/explicit/runtime"):
                    self.assertEqual(admission._measurement_eligibility(item), (True, ()))
                    self.assertEqual(admission._measurement_eligibility(item), (True, ()))
                self.assertEqual(replay.call_count, 2)
                replay.assert_called_with(item, environ=env)
        self.assertIsNone(native_gate.replay_environ())

    def test_scope_survives_nested_default_and_resets_after_exception(self):
        from oracle_grounded import native_gate
        env = {"SF_ORACLE_RUST_BIN": "/explicit/runtime"}
        failure = ValueError("simulated failure")

        def fail_inside_nested_scope():
            with native_gate.runtime_gate("/explicit/runtime"):
                with native_gate.runtime_gate(None):
                    self.assertEqual(native_gate.replay_environ(), env)
                    raise failure

        with mock.patch.object(native_gate, "runtime_environ", return_value=env):
            with self.assertRaisesRegex(ValueError, "simulated failure"):
                fail_inside_nested_scope()
        self.assertIsNone(native_gate.replay_environ())

    def test_non_native_and_wrong_family_never_use_explicit_gate(self):
        from oracle_grounded import native_gate
        with mock.patch.object(native_gate, "runtime_environ", return_value={}):
            with native_gate.runtime_gate("/explicit/runtime"):
                with mock.patch.object(record, "reproduce") as replay:
                    for item in (self.item("unknown"), self.item(family="unrelated")):
                        self.assertFalse(admission._measurement_eligibility(item)[0])
                replay.assert_not_called()

    def test_replay_mismatch_and_unavailability_block_admission(self):
        from oracle_grounded import native_gate
        with mock.patch.object(native_gate, "runtime_environ", return_value={}):
            with native_gate.runtime_gate("/explicit/runtime"):
                for status in ("mismatch", "unavailable", "invalid"):
                    with self.subTest(status=status):
                        item = self.item()
                        with mock.patch.object(record, "reproduce", return_value=(status, "reason")):
                            with self.assertRaises(admission.OracleAdmissionError):
                                admission._measurement_eligibility(item)

    def test_entrypoint_parsers_accept_explicit_executable(self):
        import compose_curated
        import export_hf
        import oracle_validate
        for parser, args in ((compose_curated.parse_args, ["in", "out"]),
                             (export_hf.parse_args, ["in", "out"]),
                             (oracle_validate.parse_args, ["in"])):
            parsed = parser(args + ["--oracle-rust-bin", "/explicit/runtime"])
            self.assertEqual(parsed.oracle_rust_bin, "/explicit/runtime")

    def test_public_entrypoints_keep_explicit_scope_through_nested_work(self):
        import compose_curated
        import export_hf
        import oracle_validate
        from oracle_grounded import native_gate
        environment = {"SF_ORACLE_RUST_BIN": "/explicit/runtime"}

        def observed(*_args, **_kwargs):
            self.assertEqual(native_gate.replay_environ(), environment)
            return {"observed": True}

        with mock.patch.object(native_gate, "runtime_environ", return_value=environment):
            with mock.patch.object(compose_curated, "_facade_delegate", side_effect=observed):
                self.assertEqual(compose_curated.compose_run("in", "out", oracle_rust_bin="chosen"),
                                 {"observed": True})
            with mock.patch.object(export_hf, "_export_request", side_effect=observed):
                self.assertEqual(export_hf.export_run("in", "out", oracle_rust_bin="chosen"),
                                 {"observed": True})
            with mock.patch.object(oracle_validate, "authenticate_manifest", return_value=None):
                with mock.patch.object(oracle_validate, "validate_run_snapshot", side_effect=observed) as validate:
                    oracle_validate.validate_run("in", oracle_rust_bin="chosen")
                self.assertTrue(validate.call_args.kwargs["options"].reproduce)
        self.assertIsNone(native_gate.replay_environ())

    def test_missing_explicit_binary_is_a_controlled_cli_failure(self):
        import contextlib
        import io
        import tempfile
        import compose_curated
        import export_hf
        import oracle_validate
        for command in (compose_curated.main, export_hf.main, oracle_validate.main):
            with self.subTest(command=command.__module__):
                with tempfile.TemporaryDirectory() as source:
                    arguments = [source]
                    if command is not oracle_validate.main:
                        arguments.append(str(Path(source) / "out"))
                    arguments += ["--oracle-rust-bin", str(Path(source) / "missing")]
                    with contextlib.redirect_stderr(io.StringIO()) as errors:
                        self.assertEqual(command(arguments), 2)
                    self.assertIn("executable", errors.getvalue())

    def test_validator_refuses_ambient_native_runtime_and_replays_reference_locally(self):
        from collections import Counter
        from types import SimpleNamespace
        from oracle_validate_records import RecordChecks
        reporter = mock.Mock()
        replay = mock.Mock(return_value=("reproduced", "digest"))
        checker = RecordChecks(SimpleNamespace(record=SimpleNamespace(reproduce=replay)))
        scope = SimpleNamespace(totals=Counter(), report=reporter)
        checker._reproduce_record(self.item(), "row:1", scope)
        replay.assert_not_called()
        self.assertEqual(scope.totals["reproduce_unavailable"], 1)
        reference = {"oracle": {"implementation": "reference"}}
        checker._reproduce_record(reference, "row:2", scope)
        replay.assert_called_once_with(reference, environ={})


if __name__ == "__main__":
    unittest.main()
