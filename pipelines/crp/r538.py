#!/usr/bin/env python3
"""CRP r538 catalog: compact JSONL extract of ``crp-mill-r538``.

``catalog.plants_from_source`` is the extract seam. This module loads the
committed ``config/crp`` header plus ``plants-r538.jsonl``. The mill script is
never vendored or executed; a live re-extract uses ``git show``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import catalog as cat
from ._contract import bind_import_twin
from . import wave_catalog

CATALOG_ID = "crp-r538-v1"
CATALOG_FORMAT = "crp-r538-catalog/1"
CATALOG_FILENAME = "CATALOG-r538.json"
PLANTS_FILENAME = "plants-r538.jsonl"
FACTORY = cat.FACTORY
GENERATOR = cat.GENERATOR
ID_PREFIX = cat.ID_PREFIX
WAVE_FIRST_ROUND = 538
PLANTS_PER_ROUND = cat.PLANTS_PER_ROUND
EXPECTED_PLANTS = 495
WAVE_LAST_ROUND = WAVE_FIRST_ROUND + (EXPECTED_PLANTS // PLANTS_PER_ROUND) - 1
RUN_FORMAT = "crp-r538-run/1"
SOURCE_REF = "legacy-mill-lane"
SOURCE_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
SOURCE_PATH = "experiments/crp-mill-r538.py"
SOURCE_METHOD = "git-show+ast.parse"
SOURCE_BLOB_SHA1 = "b46e07318769c9ca0359f4cadee1ea9d65775c3c"
SOURCE_SHA256 = "6b597a5c62f6b5f0738f5cd46ea8b09c05bc8ce32fc5ab8f7d40ea0cdb1f32d3"
SOURCE_LINES = 3653
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
