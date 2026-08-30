#!/usr/bin/env python3
"""End-to-end contract checks: seeded fixtures and the round_txn publish path.

StrictContractFixtures seeds one clean baseline and one record per rejected
rule so "exactly one ERROR" proves each rule fires for the intended reason.
TransactionalRoundPassesHardenedValidator proves the hardening is only
useful because it rejects legacy shapes without blocking the publication
path the factory actually uses.
"""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from round_txn_test_helpers import distillation_sidecars  # noqa: E402
from validate_run_test_helpers import TINY_THALAMIC, _invoke  # noqa: E402

import check_records  # noqa: E402
import round_txn  # noqa: E402

STRICT_FIXTURES = _TESTS / "fixtures" / "strict-validator"


class StrictContractFixtures(unittest.TestCase):
    """Seeded fixtures: one clean baseline, one record per rejected rule.

    Each reject fixture differs from `accept-baseline.jsonl` by exactly one
    field, so "exactly one ERROR" is the assertion that proves the rule fired
    for the intended reason.
    """

    def _fixture_result(self, name):
        with tempfile.TemporaryDirectory() as raw:
            run_dir = Path(raw) / "run"
            run_dir.mkdir()
            (run_dir / name).write_text((STRICT_FIXTURES / name).read_text())
            return _invoke(str(run_dir))

    def test_baseline_passes_both_layers(self):
        with tempfile.TemporaryDirectory() as raw:
            run_dir = Path(raw) / "run"
            run_dir.mkdir()
            (run_dir / "accept-baseline.jsonl").write_text(
                (STRICT_FIXTURES / "accept-baseline.jsonl").read_text()
            )
            shape = _invoke(str(run_dir))
            deep = check_records.check_run(run_dir, strict=True)
        self.assertEqual(shape.returncode, 0, shape.stderr)
        self.assertEqual(deep["exit_code"], 0, deep)
        self.assertEqual(deep["warnings"], [], deep)

    def test_every_reject_fixture_fails_with_exactly_one_error(self):
        fixtures = sorted(STRICT_FIXTURES.glob("reject-*.jsonl"))
        self.assertTrue(fixtures, "reject fixtures are missing")
        for path in fixtures:
            with self.subTest(fixture=path.name):
                result = self._fixture_result(path.name)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertEqual(result.stderr.strip().count("ERROR:"), 1, result.stderr)

    def test_reject_fixtures_name_the_rule_they_break(self):
        expected = {
            "reject-reward-mismatch.jsonl": "!= sum of components",
            "reject-unsorted-spikes.jsonl": "not globally non-decreasing",
            "reject-sim-or-real.jsonl": "state.sim_or_real must not be 'real'",
            "reject-missing-meta-round.jsonl": "meta.round is required",
            "reject-missing-provenance-kind.jsonl": "provenance.kind must be one of",
        }
        self.assertEqual(
            sorted(expected),
            sorted(path.name for path in STRICT_FIXTURES.glob("reject-*.jsonl")),
            "a reject fixture was added or removed without an expected message",
        )
        for name, marker in expected.items():
            with self.subTest(fixture=name):
                self.assertIn(marker, self._fixture_result(name).stderr)

    def test_reject_fixtures_differ_from_the_baseline_in_one_field(self):
        baseline = json.loads((STRICT_FIXTURES / "accept-baseline.jsonl").read_text())
        for path in sorted(STRICT_FIXTURES.glob("reject-*.jsonl")):
            with self.subTest(fixture=path.name):
                record = json.loads(path.read_text())
                self.assertEqual(sorted(record), sorted(baseline))
                differing = [
                    key
                    for key in baseline
                    # `id` differs on every fixture so the deep layer's
                    # duplicate-id check never masks the rule under test.
                    if key != "id" and record[key] != baseline[key]
                ]
                self.assertEqual(len(differing), 1, differing)

    def test_legacy_violations_are_not_silently_passed(self):
        """No silent pass: the shapes the 2026-08-19 harvest flagged still fail.

        The harvest's 112 raw errors were three classes — `sim_or_real: real`
        labels, unsorted bridge trains, and reward totals that do not
        reconcile. Legacy records carry no top-level `id` (only `meta.id`),
        which the shape layer deliberately tolerates; that tolerance must not
        extend to the invariants above.
        """
        legacy = {
            "bad-reward.jsonl": "!= sum of components",
            "bad-spikes.jsonl": "not globally non-decreasing",
        }
        fixtures = STRICT_FIXTURES.parent
        for name, marker in legacy.items():
            with self.subTest(fixture=name):
                with tempfile.TemporaryDirectory() as raw:
                    run_dir = Path(raw) / "run"
                    run_dir.mkdir()
                    (run_dir / name).write_text((fixtures / name).read_text())
                    shape = _invoke(str(run_dir))
                    deep = check_records.check_run(run_dir)
                self.assertEqual(shape.returncode, 1, shape.stderr)
                self.assertIn(marker, shape.stderr)
                self.assertEqual(deep["exit_code"], 1, deep)


class TransactionalRoundPassesHardenedValidator(unittest.TestCase):
    """A round published through round_txn must satisfy the hardened contract.

    The hardening is only useful if it rejects legacy shapes without blocking
    the publication path the factory actually uses.
    """

    def test_published_round_validates_clean(self):
        record = copy.deepcopy(TINY_THALAMIC)
        record["id"] = "txn-hardened-1"
        record["meta"] = {"factory": "thalamic-trajectory-factory", "round": 1}
        record["spike_events"] = [
            {"channel": "a", "t_rel_ms": 1.0, "amplitude": 0.4},
            {"channel": "b", "t_rel_ms": 2.0, "amplitude": 0.6},
        ]
        record.update(distillation_sidecars())
        # Execution verification (pipelines/round_txn_execution.py) blocks
        # publish on an unverifiable future_outcome; give it well-formed
        # observable evidence so this test exercises the shape/deep
        # validators it targets rather than the execution gate.
        record["future_outcome"] = {
            "success": "full",
            "timeline": [{"t_ms": 0, "event": "noop accepted"}],
            "observed_effects": ["no actuator motion"],
            "new_state": {"sim_or_real": "designed", "domain": "gate-test"},
        }
        with tempfile.TemporaryDirectory() as raw:
            factory = Path(raw) / "outputs" / "raw" / "2099-01-01" / "thalamic-trajectory-factory"
            factory.mkdir(parents=True)
            reservation = round_txn.reserve(factory, 1, 1)
            stage = Path(reservation["staging_dir"])
            (stage / reservation["batch_file"]).write_text(json.dumps(record) + "\n")
            (stage / reservation["notes_file"]).write_text(
                "# Self-critique\n\nBounded fixture round.\n\nNovel coverage: 100%\n"
            )
            manifest = round_txn.publish(factory, 1, reservation["token"])
            self.assertEqual(manifest["records"], 1)

            shape = _invoke(str(factory))
            deep = check_records.check_run(factory, strict=True)

        self.assertEqual(shape.returncode, 0, shape.stderr)
        self.assertEqual(deep["exit_code"], 0, deep)


if __name__ == "__main__":
    unittest.main()
