"""Regressions for oracle provenance, preserved payloads, and input bounds."""

import copy
import os
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

import oracle_generate
import curate_identity
import curate_identity_checks
from oracle_grounded import families, record, sim
from oracle_fixture_replay import replay_diagnostic_fixture


class OracleBoundaryTests(unittest.TestCase):
    def test_historical_replay_cannot_claim_resolved_checkout_provenance(self):
        for dirty in (False, True):
            with self.subTest(dirty=dirty):
                with self.assertRaisesRegex(ValueError, "unresolved provenance"):
                    replay_diagnostic_fixture({"oracle_dirty": dirty}, Path("unused"))

    def test_reference_stamp_matches_checkout(self):
        with (
            mock.patch.object(oracle_generate.oracles, "resolve_commit", return_value=("a" * 40, False)),
            mock.patch.object(oracle_generate.oracles, "resolve_source_commit", return_value="b" * 40),
        ):
            self.assertTrue(oracle_generate._stamp_contradicts_checkout(
                "b" * 40, {"runtimes": [{"bound": False}]}
            ))

    def test_explicit_stamp_requires_an_authenticated_checkout(self):
        with (
            mock.patch.object(oracle_generate.oracles, "resolve_commit", return_value=("unknown", None)),
            mock.patch.object(oracle_generate.oracles, "resolve_source_commit", return_value="b" * 40),
        ):
            self.assertTrue(oracle_generate._stamp_contradicts_checkout(
                "b" * 40, {"runtimes": [{"bound": False}]}
            ))

    def test_preserving_writer_keeps_original_oracle_line(self):
        original = '{ "number" : 1.00 }'
        result = SimpleNamespace(
            action="retained", record={"number": 1.0},
            mapping={"record_kind": "oracle", "source": {
                "path": "oracle-grounded/accepted.jsonl", "line": 1, "original": original,
            }},
        )
        retained = curate_identity_checks.retained_source_lines(
            [result], curate_identity._identity_check_dependencies()
        )
        self.assertEqual(retained["oracle-grounded/accepted.jsonl"][1], original)

    def test_record_seed_has_one_canonical_unsigned_representation(self):
        item = record.build_record(families.ENCODER_FAMILY, 0, 7)
        for seed in (-1, 2 ** 64):
            with self.subTest(seed=seed):
                malformed = copy.deepcopy(item)
                malformed["generator"]["seed"] = seed
                malformed["oracle"]["seed"] = seed
                findings = record._validate_generator_side(malformed)
                self.assertTrue(any("64-bit" in finding for finding in findings), findings)

    def test_refractory_inhibition_survives_until_recurrent_spike(self):
        nodes = [sim.mesh_node("A", t_refractory_ms=2.0)]
        edges = [{"src": "A", "dst": "A", "weight": 1.2, "delay_ms": 3.0}]
        cue = {"target": "A", "t_ms": 1.0, "amplitude": 2.0}
        reset = {"target": "A", "t_ms": 1.5, "amplitude": -2.0}
        held = sim.simulate_mesh(nodes, edges, [cue], 20.0)
        cleared = sim.simulate_mesh(nodes, edges, [cue, reset], 20.0)
        self.assertGreater(held["spike_counts"]["A"], 1)
        self.assertEqual(cleared["spike_counts"]["A"], 1)

    def test_untrusted_excerpt_is_bounded_before_event_findings(self):
        item = record.build_record(families.ENCODER_FAMILY, 0, 7)
        item["oracle"]["implementation"] = "named-runtime"
        state = item["result"]["measured"]["encoding_a"]
        state["representation_excerpt"] = [{"channel": "unknown", "t_ms": -1}] * 1000
        findings = families._encoder_checks(item)
        self.assertLess(len(findings), 100)
        self.assertTrue(any("excerpt bound" in finding for finding in findings), findings)

    def test_generation_stops_at_byte_limit_before_retaining_remaining_records(self):
        with (
            mock.patch.object(oracle_generate, "MAX_JSONL_BYTES", 1),
            mock.patch.object(oracle_generate.record, "build_record", wraps=record.build_record) as build,
        ):
            with self.assertRaisesRegex(ValueError, "per-file limit"):
                oracle_generate.generate_family(
                    families.ENCODER_FAMILY, 3, 7, 1, None, None, False
                )
        self.assertEqual(build.call_count, 1)

    def test_staging_family_symlink_cannot_redirect_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "staging"
            outside = Path(tmp) / "outside"
            root.mkdir()
            outside.mkdir()
            (root / "family").symlink_to(outside, target_is_directory=True)
            descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
            try:
                with self.assertRaises(OSError):
                    oracle_generate.write_jsonl(
                        Path("family/accepted.jsonl"), [{"sample": 1}], root_fd=descriptor
                    )
            finally:
                os.close(descriptor)
            self.assertEqual(list(outside.iterdir()), [])

    def test_family_swap_between_creation_and_open_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "staging"
            outside = Path(tmp) / "outside"
            root.mkdir()
            outside.mkdir()
            descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
            mkdir = os.mkdir

            def swap(component, *args, **kwargs):
                mkdir(component, *args, **kwargs)
                (root / component).rmdir()
                (root / component).symlink_to(outside, target_is_directory=True)

            try:
                with mock.patch.object(oracle_generate.os, "mkdir", side_effect=swap):
                    with self.assertRaises(OSError):
                        oracle_generate.write_jsonl(
                            Path("family/accepted.jsonl"), [{"sample": 1}], root_fd=descriptor
                        )
                with self.assertRaises(OSError):
                    oracle_generate._verify_staged_payloads(
                        descriptor, {"family/accepted.jsonl": {"sha256": "0" * 64}}, 100
                    )
            finally:
                os.close(descriptor)
            self.assertEqual(list(outside.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
