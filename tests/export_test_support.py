#!/usr/bin/env python3
"""Shared fixtures and helpers for the curated-export test modules.

Split out of ``test_export_hf`` so each test module can state one
responsibility. Not named ``test_*`` so it is not itself collected.
"""

import importlib.util
import json
import sys
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parents[0]
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(REPO / "pipelines"))

import compose_curated  # noqa: E402
import training_audit  # noqa: E402
from rights_record import BLOCKER_PREFIX  # noqa: E402

from compose_curated_test_support import build_source_run  # noqa: E402

HAS_PYARROW = importlib.util.find_spec("pyarrow") is not None


def strip_rights_blockers(report):
    """Drop ``rights:`` blockers so writer tests can exercise export mechanics."""

    blockers = [
        item for item in report.get("blockers", []) if not str(item).startswith(BLOCKER_PREFIX)
    ]
    patched = dict(report)
    patched["blockers"] = blockers
    if list(report.get("blockers") or []) != blockers:
        patched["training_ready"] = not blockers
    return patched


@contextmanager
def allow_research_only_export():
    """Strip rights blockers from the live audit used by compose and export."""

    real = training_audit.audit_run

    def patched(run_dir, snapshot=None, completion_source=None):
        return strip_rights_blockers(real(run_dir, snapshot=snapshot, completion_source=completion_source))

    with mock.patch.object(training_audit, "audit_run", patched):
        yield


class ResearchExportAllowed:
    """Writer tests that compose hosted records still need an exportable audit."""

    def run(self, result=None):
        with allow_research_only_export():
            return super().run(result)


def compose_fixture(root):
    """Compose the shared four-factory fixture and return the curated root."""

    source = build_source_run(Path(root) / "run")
    curated = Path(root) / "curated"
    compose_curated.compose_run(compose_curated.ComposeRunContext(source, curated))
    return curated


def calibration_document(*records):
    """A reward-calibration sidecar in the shape the export authenticates."""

    return json.dumps({"records": list(records)}, ensure_ascii=False) + "\n"


ONE_CALIBRATION = calibration_document(
    {"usd_conversion_factor": 0.5, "scope": "applies to ffpc-r5-002"}
)
