#!/usr/bin/env python3
"""Trusted limit evidence and candidate-level crash classification."""

import sys
import types
import unittest
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from code_repair_test_support import executor as ex, generate, refusal, vocabulary as cv  # noqa: E402
from code_repair import _harness as harness  # noqa: E402

RUNNER = ex.Executor(timeout_s=5.0)


def _serving(report):
    """A `_State` stand-in whose executor always answers with `report`.

    `generate._run_phase` only reaches `state.executor.run`, so this is the whole
    surface those tests need.
    """

    return types.SimpleNamespace(executor=types.SimpleNamespace(run=lambda _job: report))



class SandboxFailures(unittest.TestCase):
    def test_attested_crash_without_environment_is_a_candidate_harness_error(self):
        """The trusted attestation survives a crash that loses the JSON environment."""

        job = ex.Job("mutant:test", "def f():\n    pass\n", "f")
        for environment in (None, "gone", {}, {"python": "3.14"}):
            with self.subTest(environment=environment):
                body = {"protocol": cv.HARNESS_PROTOCOL,
                        "load": {"status": "error", "error": "HarnessError: MemoryError: "}}
                if environment is not None:
                    body["environment"] = environment
                report = ex._parse_report(
                    job, 0, f"{ex.LIMITS_ATTESTATION_PREFIX}true\n".encode(),
                    json.dumps(body).encode())
                self.assertEqual(report.status, cv.PHASE_HARNESS_ERROR)
                self.assertIn("MemoryError", report.detail)
                self.assertNotIn(cv.FINDING_SANDBOX_UNAVAILABLE, report.detail)
                self.assertIs(generate._run_phase(_serving(report), job), report)

    def test_trusted_false_attestation_refuses_even_when_json_claims_true(self):
        """An explicit setup failure survives as structured parent-owned evidence."""

        job = ex.Job("mutant:test", "def f():\n    pass\n", "f")
        body = json.dumps({"protocol": cv.HARNESS_PROTOCOL,
                           "environment": {"limits_applied": True},
                           "load": {"status": "ok"}, "public": [], "hidden": []}).encode()
        report = ex._parse_report(
            job, 0, f"{ex.LIMITS_ATTESTATION_PREFIX}false\n".encode(), body)
        self.assertEqual(report.status, cv.PHASE_HARNESS_ERROR)
        self.assertIs(report.environment.get("limits_applied"), False)
        with refusal(self, cv.FINDING_SANDBOX_UNAVAILABLE):
            generate._run_phase(_serving(report), job)

    def test_trusted_setup_failure_refuses_even_when_report_or_exit_is_broken(self):
        """Negative setup evidence is authoritative before JSON parsing or exit checks."""

        job = ex.Job("mutant:test", "def f():\n    pass\n", "f")
        for returncode, body in ((0, b""), (0, b"not json"), (0, b"{}"), (1, b"")):
            with self.subTest(returncode=returncode, body=body):
                report = ex._parse_report(
                    job, returncode, f"{ex.LIMITS_ATTESTATION_PREFIX}false\n".encode(), body)
                self.assertIs(report.environment.get("limits_applied"), False)
                with refusal(self, cv.FINDING_SANDBOX_UNAVAILABLE):
                    generate._run_phase(_serving(report), job)

    def test_a_program_cannot_stop_the_run_by_naming_the_finding_in_its_own_error(self):
        """`detail` carries program-controlled prose; the refusal must not read it.

        A program raising ``SANDBOX_UNAVAILABLE: ...`` reports limits applied and
        must cost only its own candidate, not the whole run.
        """

        module = (
            f'raise ValueError("{cv.FINDING_SANDBOX_UNAVAILABLE}: injected")'
            "\n\n\ndef f():\n    return 1\n"
        )
        job = ex.Job("mutant:test", module, "f")
        report = RUNNER.run(job)
        self.assertIn(cv.FINDING_SANDBOX_UNAVAILABLE, report.detail)
        self.assertTrue(report.environment.get("limits_applied"))
        served = _serving(report)
        self.assertIs(generate._run_phase(served, job), report)

    def test_every_non_true_injected_limits_claim_refuses_the_run(self):
        """Injected executors must meet the same structural contract."""

        job = ex.Job("mutant:test", "def f():\n    pass\n", "f")
        for flag in (False, None, 1, "true"):
            with self.subTest(flag=flag):
                report = ex.PhaseReport(cv.PHASE_HARNESS_ERROR, False, (), (),
                                        {"limits_applied": flag}, "")
                with refusal(self, cv.FINDING_SANDBOX_UNAVAILABLE):
                    generate._run_phase(_serving(report), job)

    def test_a_phase_that_ran_must_claim_the_limits_even_from_an_injected_executor(self):
        """`run` takes an injected executor; a PHASE_OK phase with no claim is unstorable.

        `record_validation._phase_runtime_contract` stores a `PHASE_OK` phase only
        when `limits_applied` is True, load error or not, so letting one through
        would build a record that fails its own validation. A load error is
        `PHASE_OK` with `ok` False, which is why the status and not `ok` is the
        test here (Codex on #212, twice).
        """

        job = ex.Job("mutant:test", "def f():\n    pass\n", "f")
        rows = ({"id": "hidden:0", "status": "pass"},)
        unclaimed = ({}, {"python": "3.14"}, {"limits_applied": None})
        for environment in unclaimed:
            for ran_ok, body in ((True, rows), (False, ())):
                with self.subTest(environment=environment, load_ok=ran_ok):
                    phase = ex.PhaseReport(cv.PHASE_OK, ran_ok, (), body, dict(environment), "")
                    with refusal(self, cv.FINDING_SANDBOX_UNAVAILABLE):
                        generate._run_phase(_serving(phase), job)
        for ran_ok, body in ((True, rows), (False, ())):
            claimed = ex.PhaseReport(cv.PHASE_OK, ran_ok, (), body, {"limits_applied": True}, "")
            self.assertIs(generate._run_phase(_serving(claimed), job), claimed)

    def test_a_setrlimit_refusal_is_reported_as_an_environment_not_thrown(self):
        """A refused limit must reach the parent as evidence, not as a bare crash."""

        spec = {"cpu_seconds": 1, "address_space_bytes": 1 << 20, "file_size_bytes": 1 << 10}
        for broken in (spec | {"cpu_seconds": "x"}, spec | {"file_size_bytes": None}, {}):
            with self.subTest(spec=broken):
                self.assertFalse(harness._apply_limits(broken))


