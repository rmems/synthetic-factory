#!/usr/bin/env python3
"""Shared surface for ``test_crp_*`` wave modules (package-tree checks)."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
COMMITTED = REPO / "config" / "crp"
PACKAGE = PIPELINES / "crp"

PACKAGE_PY = (
    "__init__.py",
    "_contract.py",
    "catalog.py",
    "cli.py",
    "generate.py",
    "leftover3_prior.py",
    "r432.py",
    "r538.py",
    "r729.py",
    "r817.py",
    "r995.py",
    "wave_catalog.py",
)

__all__ = (
    "COMMITTED",
    "PACKAGE",
    "PACKAGE_PY",
    "PIPELINES",
    "REPO",
    "package_py_names",
    "vendored_mill_script_hits",
)


def vendored_mill_script_hits(
    package: Path = PACKAGE,
    committed: Path = COMMITTED,
) -> list[Path]:
    """Paths that would mean a mill/loop script was vendored into the package tree."""

    hits = list(package.rglob("crp-mill*.py"))
    hits.extend(package.rglob("crp-loop*.py"))
    hits.extend(package.rglob("_gen_crp*.py"))
    hits.extend(committed.rglob("*mill*.py"))
    hits.extend(committed.rglob("*loop*.py"))
    return hits


def package_py_names(package: Path = PACKAGE) -> tuple[str, ...]:
    """Sorted top-level ``*.py`` basenames under the CRP package."""

    return tuple(sorted(path.name for path in package.glob("*.py")))
