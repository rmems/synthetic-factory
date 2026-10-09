#!/usr/bin/env python3
"""Shared helpers for the tool-world test modules.

Tests load packs straight from the committed catalog directory and build
private catalogs in temporary directories, so a pack whose pin is not yet in
``CATALOG.json`` is still testable and the committed pins are never edited by
a test.
"""

from __future__ import annotations

import contextlib
import json
import shutil
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

from tool_world import catalog as catalog_mod  # noqa: E402
from tool_world import env as env_mod  # noqa: E402
from tool_world import pack as pack_mod  # noqa: E402
from tool_world import vocabulary as cv  # noqa: E402

CATALOG_DIR = catalog_mod.DEFAULT_CATALOG
PRODUCED_AT = "2026-10-09T00:00:00Z"

__all__ = [
    "CATALOG_DIR",
    "PRODUCED_AT",
    "catalog_mod",
    "cv",
    "env_mod",
    "load_pack",
    "make_env",
    "pack_mod",
    "private_catalog",
    "refusal",
]


def load_pack(pack_id: str) -> pack_mod.Pack:
    """The committed pack with that id, loaded without consulting CATALOG.json pins."""
    return pack_mod.load_pack(CATALOG_DIR / pack_id)


def make_env(pack_id: str, task_id: str, seed: int = 0) -> env_mod.Environment:
    pack = load_pack(pack_id)
    return env_mod.Environment(pack, pack.task(task_id), seed)


def private_catalog(root: Path, pack_ids: tuple[str, ...]) -> Path:
    """Copy the named committed packs into ``root`` and pin them in a fresh CATALOG.json."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    rows = []
    for pack_id in pack_ids:
        destination = root / pack_id
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(CATALOG_DIR / pack_id, destination)
        loaded = pack_mod.load_pack(destination)
        rows.append({"pack_id": loaded.pack_id, "pack_sha256": loaded.pack_sha256})
    header = {
        "catalog_id": "tool-world-test",
        "format": cv.CATALOG_FORMAT,
        "family": cv.FAMILY,
        "packs": rows,
    }
    (root / catalog_mod.CATALOG_FILENAME).write_text(json.dumps(header, indent=2) + "\n", encoding="utf-8")
    return root


@contextlib.contextmanager
def refusal(case: unittest.TestCase, code: str, needle: str | None = None):
    """Assert the block raises a tool-world refusal with ``code`` (and ``needle`` in its prose)."""
    with case.assertRaises(cv.ToolWorldRefusal) as caught:
        yield caught
    case.assertEqual(caught.exception.code, code)
    if needle is not None:
        case.assertIn(needle, str(caught.exception))
