#!/usr/bin/env python3
"""CRP r729 catalog: compact JSONL extract of ``crp-mill-r729``.

``catalog.plants_from_source`` is the extract seam. This module loads the
committed ``config/crp`` header plus ``plants-r729.jsonl``. The mill script is
never vendored or executed; a live re-extract uses ``git show``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import catalog as cat
from ._contract import bind_import_twin
from . import wave_catalog

CATALOG_ID = "crp-r729-v1"
CATALOG_FORMAT = "crp-r729-catalog/1"
CATALOG_FILENAME = "CATALOG-r729.json"
PLANTS_FILENAME = "plants-r729.jsonl"
FACTORY = cat.FACTORY
GENERATOR = cat.GENERATOR
ID_PREFIX = cat.ID_PREFIX
WAVE_FIRST_ROUND = 729
PLANTS_PER_ROUND = cat.PLANTS_PER_ROUND
EXPECTED_PLANTS = 216
WAVE_LAST_ROUND = WAVE_FIRST_ROUND + (EXPECTED_PLANTS // PLANTS_PER_ROUND) - 1
RUN_FORMAT = "crp-r729-run/1"
SOURCE_REF = "legacy-mill-lane"
SOURCE_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
SOURCE_PATH = "experiments/crp-mill-r729.py"
SOURCE_METHOD = "git-show+ast.parse"
SOURCE_BLOB_SHA1 = "0be2c17f6ca22b0a773589380fe4d86299fdb35f"
SOURCE_SHA256 = "1a090e78cc23f04ba93be3d49518260e1de9480cdf87d65e07dffbdfe64148d1"
SOURCE_LINES = 1505
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
