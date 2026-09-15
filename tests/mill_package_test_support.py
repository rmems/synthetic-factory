#!/usr/bin/env python3
"""Shared surface for the ``test_mill_package_*`` modules."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from coded_refusal_test_support import CodedFamily, coded_refusal
from mill_package_import_probe import MODULES as FAMILY_MODULES

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "pipelines") not in sys.path:
    sys.path.insert(0, str(REPO / "pipelines"))

from mill import catalog_load, cli, generate, publication, records, validation, vocabulary
from mill._contract import load_strict_json

FIXTURE_CATALOG = REPO / "catalogs" / "mill"
PINNED_AT = "2026-09-15T00:00:00.000Z"
SEED = 20260915
MILL_FAMILY = CodedFamily(
    vocabulary.MillRefusal, vocabulary.FINDING_CODE_SET, vocabulary.REASON_CODE_SET
)

__all__ = (
    "FAMILY_MODULES",
    "FIXTURE_CATALOG",
    "MILL_FAMILY",
    "PINNED_AT",
    "REPO",
    "SEED",
    "catalog_load",
    "cli",
    "generate",
    "load_strict_json",
    "publication",
    "records",
    "refusal",
    "validation",
    "vocabulary",
)


def refusal(case, code, *fragments):
    """Assert a ``MillRefusal`` carrying exactly ``code`` and every prose fragment."""
    return coded_refusal(case, MILL_FAMILY, code, *fragments)
