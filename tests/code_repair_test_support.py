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
import dataclasses
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from coded_refusal_test_support import CodedFamily, coded_refusal
from code_repair_import_probe import MODULES as FAMILY_MODULES
from distill_contract_test_support import REPO, envelope, oc
from code_repair import catalog, cli, executor, generate, mutate, records, verify, views, vocabulary

FIXTURE_CATALOG = REPO / "tests" / "fixtures" / "code-repair"
PINNED_AT = "2026-09-08T00:00:00.000Z"
SEED = 20260908
REPAIR_FAMILY = CodedFamily(
    vocabulary.RepairRefusal, vocabulary.FINDING_CODE_SET, vocabulary.REASON_CODE_SET
)

__all__ = (
    "FAMILY_MODULES", "FIXTURE_CATALOG", "FakeExecutor", "PINNED_AT", "REPO", "SEED", "catalog",
    "boundary_site", "cli", "envelope", "executor", "fixture", "generate", "mutate", "oc", "program",
    "records",
    "refusal", "report", "rows", "smoke_run", "verify", "views", "vocabulary",
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


def boundary_site(prog, text=None):
    """The program's single comparison-boundary site (the S1 operator), on ``text`` if given."""

    found = mutate.sites(prog.text if text is None else text, prog.function, prog.want_kind)
    (site,) = [s for s in found if s.operator == vocabulary.OPERATOR_COMPARISON_BOUNDARY]
    return site


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
        if phase == 'original_repeat' and phase not in self.by_phase:
            phase = 'original'
        self.log.append({"label": job.label, "status": "fake"})
        if phase == vocabulary.PHASE_REFERENCE and phase not in self.by_phase:
            # Unless a test says otherwise, the certifying reference answers every pinned case.
            return dataclasses.replace(report((), rows("hidden", len(job.cases))),
                                       module_sha256=catalog.sha256_text(job.module_text))
        canned = self.by_phase[phase]
        result = canned(job) if callable(canned) else canned
        return dataclasses.replace(result, module_sha256=catalog.sha256_text(job.module_text))


@functools.lru_cache(maxsize=None)
def smoke_run(seed=SEED, count=12):
    """One real generation run into a temporary directory: ``(summary, records, run_dir)``."""

    root = Path(tempfile.mkdtemp(prefix="code-repair-smoke-"))
    out = root / "run"
    request = generate.RunRequest(FIXTURE_CATALOG, out, seed, count, PINNED_AT)
    summary = generate.run(request)
    loaded = [record for _lineno, record in oc.read_jsonl(out / generate.CANDIDATES_FILENAME)]
    return summary, loaded, out
