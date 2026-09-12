#!/usr/bin/env python3
"""Shared surface for the ``test_code_repair_*`` modules (software lane, S1).

The fixture catalog, the flat-spelling family modules, a fake executor that
serves canned phase reports (so the decision table, the record assembly and
the views are tested without a subprocess), the real short-timeout executor,
the coded-refusal assertion and a memoised smoke run -- carried once so the
direct test modules stay small and qlty's duplication smells stay silent.
Fake-executor evidence and real-subprocess evidence are kept apart: only
``smoke_run()`` and the harness/executor tests spawn interpreters.
"""

import functools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from coded_refusal_test_support import CodedFamily, coded_refusal
from distill_contract_test_support import REPO, envelope, oc
from code_repair import catalog, cli, executor, vocabulary

FIXTURE_CATALOG = REPO / "tests" / "fixtures" / "code-repair"
PINNED_AT = "2026-09-08T00:00:00.000Z"
SEED = 20260908
REPAIR_FAMILY = CodedFamily(
    vocabulary.RepairRefusal, vocabulary.FINDING_CODE_SET, vocabulary.REASON_CODE_SET
)
FAMILY_MODULES = ("_contract", "vocabulary", "catalog", "catalog_load", "executor", "cli")

__all__ = (
    "FAMILY_MODULES", "FIXTURE_CATALOG", "FakeExecutor", "PINNED_AT", "REPO", "SEED", "catalog",
    "cli", "envelope", "executor", "fixture", "oc", "program", "refusal", "report", "rows",
    "vocabulary",
)


def refusal(case, code, *fragments):
    """Assert a ``RepairRefusal`` carrying exactly ``code`` and every prose fragment."""

    return coded_refusal(case, REPAIR_FAMILY, code, *fragments)


@functools.lru_cache(maxsize=None)
def fixture():
    """The fixture catalog, loaded once."""

    return catalog.load_catalog(FIXTURE_CATALOG)


def program(function):
    """The fixture program whose target function has this name."""

    return next(p for p in fixture().programs if p.function == function)


def rows(prefix, count, failing=(), got="wrong"):
    """``count`` rows ``prefix:0..`` that pass, except the listed indexes which fail."""

    return tuple(
        {"id": f"{prefix}:{index}", "status": "fail", "got": got}
        if index in failing else {"id": f"{prefix}:{index}", "status": "pass"}
        for index in range(count)
    )


def report(public=(), hidden=(), failure=None, detail=""):
    """A canned phase report; ``failure`` is None, "timeout", "harness_error" or "load"."""

    environment = {
        "python": "3.14.7", "implementation": "cpython", "platform": "linux",
        "limits_applied": True,
    }
    status = "ok" if failure in (None, "load") else failure
    return executor.PhaseReport(
        status, failure is None, tuple(public), tuple(hidden), environment, detail
    )


class FakeExecutor:
    """Serves canned reports by job-label phase; records every job like the real one."""

    def __init__(self, by_phase, timeout_s=2.0):
        self.by_phase = dict(by_phase)
        self.timeout_s = timeout_s
        self.harness_sha256 = executor.harness_sha256()
        self.log = []
        self.jobs = []

    def run(self, job):
        self.jobs.append(job)
        phase = job.label.split(":", 1)[0]
        self.log.append({"label": job.label, "status": "fake"})
        canned = self.by_phase[phase]
        return canned(job) if callable(canned) else canned
