#!/usr/bin/env python3
"""Compatibility shim for the pre-split shared card-schema test surface.

``card_schema.py`` was split into sibling modules and re-exported from a thin
shim so ``import card_schema`` kept working. The test module was split the same
way, but no shim was left behind -- and every open per-dataset card branch does
``import test_card_schema as _shared`` to borrow the shared fixtures. This
restores that surface so those leaf tests keep importing after the split.
"""

from test_card_schema_integration import (  # noqa: F401
    LONG_HORIZON,
    MINIMAL,
    Path,
    REPO,
    card_schema,
    io,
    json,
    mock,
    publisher,
    redirect_stderr,
    redirect_stdout,
    sys,
    tempfile,
    unittest,
    write_declaration,
)

__all__ = (
    "LONG_HORIZON",
    "MINIMAL",
    "Path",
    "REPO",
    "card_schema",
    "io",
    "json",
    "mock",
    "publisher",
    "redirect_stderr",
    "redirect_stdout",
    "sys",
    "tempfile",
    "unittest",
    "write_declaration",
)
