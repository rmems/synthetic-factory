#!/usr/bin/env python3
"""CRP r432 catalog: compact JSONL extract of ``crp-mill-r432``.

``catalog.plants_from_source`` is the extract seam. This module loads the
committed ``config/crp`` header plus ``plants.jsonl``. The mill script is
never vendored or executed; a live re-extract uses ``git show``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import catalog as cat
from ._contract import bind_import_twin
from . import wave_catalog

CATALOG_ID = "crp-r432-v1"
CATALOG_FORMAT = "crp-r432-catalog/1"
CATALOG_FILENAME = "CATALOG.json"
PLANTS_FILENAME = "plants.jsonl"
FACTORY = cat.FACTORY
GENERATOR = cat.GENERATOR
ID_PREFIX = cat.ID_PREFIX
WAVE_FIRST_ROUND = 432
PLANTS_PER_ROUND = cat.PLANTS_PER_ROUND
EXPECTED_PLANTS = 366
WAVE_LAST_ROUND = WAVE_FIRST_ROUND + (EXPECTED_PLANTS // PLANTS_PER_ROUND) - 1
RUN_FORMAT = "crp-r432-run/1"
SOURCE_REF = "legacy-mill-lane"
SOURCE_COMMIT = "9237367ce58fb8d472e5fbc18e5dbffff35bca76"
SOURCE_PATH = "experiments/crp-mill-r432.py"
SOURCE_METHOD = "git-show+ast.parse"
SOURCE_BLOB_SHA1 = "5d786849a4cd323e860f4d69708a13039e78c03e"
SOURCE_SHA256 = "35fb74a24aa9ba08d77a977c5400734b036a7527c344055859c94c674b9b32b2"
SOURCE_LINES = 3029
DEFAULT_CATALOG_DIR = Path(__file__).resolve().parents[2] / "config" / "crp"

CATALOG_META_KEYS = wave_catalog.CATALOG_META_KEYS

__all__ = [
    "CATALOG_ID", "CATALOG_META_KEYS", "DEFAULT_CATALOG_DIR", "EXPECTED_PLANTS",
    "FACTORY", "GENERATOR", "PLANTS_FILENAME", "RUN_FORMAT", "SOURCE_COMMIT",
    "SOURCE_PATH", "SOURCE_SHA256", "WAVE_FIRST_ROUND", "WAVE_LAST_ROUND",
    "catalog_check", "default_catalog_dir", "git_show_source", "load_catalog",
    "plants_for_round",
]


def _spec() -> wave_catalog.WaveSpec:
    # Build from live wrapper globals: DEFAULT_CATALOG_DIR remains a supported
    # fixture seam, while each call still receives an immutable wave snapshot.
    return wave_catalog.WaveSpec(
        name=__name__.rsplit(".", 1)[-1],
        catalog_id=CATALOG_ID,
        catalog_format=CATALOG_FORMAT,
        catalog_filename=CATALOG_FILENAME,
        plants_filename=PLANTS_FILENAME,
        wave_first_round=WAVE_FIRST_ROUND,
        wave_last_round=WAVE_LAST_ROUND,
        source_ref=SOURCE_REF,
        source_commit=SOURCE_COMMIT,
        source_path=SOURCE_PATH,
        source_method=SOURCE_METHOD,
        source_blob_sha1=SOURCE_BLOB_SHA1,
        source_sha256=SOURCE_SHA256,
        source_lines=SOURCE_LINES,
        default_catalog_dir=DEFAULT_CATALOG_DIR,
    )


def default_catalog_dir() -> Path:
    return DEFAULT_CATALOG_DIR


def git_show_source(path: str = SOURCE_PATH) -> str:
    """Return mill source via ``git show``. Never import or execute the mill."""
    return wave_catalog.git_show_source(_spec(), path)


def load_catalog(directory: Path | None = None) -> cat.Catalog:
    return wave_catalog.load_catalog(_spec(), directory)


def catalog_check(directory: Path | None = None) -> dict[str, Any]:
    """Fail closed unless every row has noun, unique identity, and a 3-stride."""
    return wave_catalog.catalog_check(_spec(), directory)


def plants_for_round(
    round_n: int,
    plants: tuple[cat.Plant, ...] | None = None,
) -> tuple[cat.Plant, ...]:
    return wave_catalog.plants_for_round(_spec(), round_n, plants)


_CATALOG = load_catalog()

bind_import_twin(__name__)
