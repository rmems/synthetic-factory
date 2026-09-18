#!/usr/bin/env python3
"""CRP r817 catalog: compact JSONL extract of ``crp-mill-r817``.

``catalog.plants_from_source`` is the extract seam. This module loads the
committed ``config/crp`` header plus ``plants-r817.jsonl``. The mill script is
never vendored or executed; a live re-extract uses ``git show``.
"""

from __future__ import annotations

import hashlib
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from . import catalog as cat
from ._contract import (
    FINDING_AST_NOT_A_PLANT,
    FINDING_CATALOG_EMPTY,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_CATALOG_TRIPLE_STRIDE,
    FINDING_DUPLICATE_FAMILY,
    FINDING_DUPLICATE_SLUG,
    FINDING_FIELD_INVALID,
    FINDING_FIELD_MISSING,
    FINDING_NOUN_MISSING,
    FINDING_PLANTS_SHA_MISMATCH,
    FINDING_ROUND_OUT_OF_DOMAIN,
    FINDING_TRIPLE_OUT_OF_DOMAIN,
    bind_import_twin,
    load_strict_json,
    refuse,
    refuse_first,
    refuse_when,
    repo_root,
    shown,
)

CATALOG_ID = "crp-r817-v1"
CATALOG_FORMAT = "crp-r817-catalog/1"
CATALOG_FILENAME = "CATALOG-r817.json"
PLANTS_FILENAME = "plants-r817.jsonl"
FACTORY = cat.FACTORY
GENERATOR = cat.GENERATOR
ID_PREFIX = cat.ID_PREFIX
WAVE_FIRST_ROUND = 817
PLANTS_PER_ROUND = cat.PLANTS_PER_ROUND
EXPECTED_PLANTS = 534
WAVE_LAST_ROUND = WAVE_FIRST_ROUND + (EXPECTED_PLANTS // PLANTS_PER_ROUND) - 1
RUN_FORMAT = "crp-r817-run/1"
SOURCE_REF = "legacy-mill-lane"
SOURCE_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
SOURCE_PATH = "experiments/crp-mill-r817.py"
SOURCE_METHOD = "git-show+ast.parse"
SOURCE_BLOB_SHA1 = "ce27c89f7799e5508a3e8d8e2f068da972285aaf"
SOURCE_SHA256 = "b3da74de1071c0c5dd472c7fb0c5de42de5a2a9ccd11a62ef9204f108e51e616"
SOURCE_LINES = 3429
DEFAULT_CATALOG_DIR = Path(__file__).resolve().parents[2] / "config" / "crp"

CATALOG_META_KEYS = (
    "catalog_id",
    "extraction",
    "family",
    "factory",
    "format",
    "generator",
    "intended_use",
    "plant_count",
    "plants_filename",
    "plants_sha256",
    "project_training_policy",
    "quota_per_round",
    "record_kind",
    "slice",
    "source_blob_sha1",
    "source_commit",
    "source_lines",
    "source_method",
    "source_path",
    "source_ref",
    "source_sha256",
    "wave_first_round",
    "wave_last_round",
)

__all__ = [
    "CATALOG_ID",
    "CATALOG_META_KEYS",
    "DEFAULT_CATALOG_DIR",
    "EXPECTED_PLANTS",
    "FACTORY",
    "GENERATOR",
    "PLANTS_FILENAME",
    "RUN_FORMAT",
    "SOURCE_COMMIT",
    "SOURCE_PATH",
    "SOURCE_SHA256",
    "WAVE_FIRST_ROUND",
    "WAVE_LAST_ROUND",
    "catalog_check",
    "default_catalog_dir",
    "git_show_source",
    "load_catalog",
    "plants_for_round",
]


def default_catalog_dir() -> Path:
    return DEFAULT_CATALOG_DIR


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def git_show_source(path: str = SOURCE_PATH) -> str:
    """Return mill source via ``git show``. Never import or execute the mill."""

    tried: list[str] = []
    for ref in (f"origin/{SOURCE_REF}", SOURCE_COMMIT, SOURCE_REF):
        spec = f"{ref}:{path}"
        tried.append(spec)
        proc = subprocess.run(
            ["git", "show", spec],
            cwd=repo_root(),
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            continue
        digest = _sha256_bytes(proc.stdout)
        refuse_when(
            digest != SOURCE_SHA256,
            FINDING_AST_NOT_A_PLANT,
            f"{spec} sha256 {digest} != pinned {SOURCE_SHA256}",
        )
        return proc.stdout.decode("utf-8")
    refuse(
        FINDING_AST_NOT_A_PLANT,
        f"legacy-mill-lane pin is not fetchable ({', '.join(tried)})",
    )


def _check_unique(plants: tuple[cat.Plant, ...]) -> None:
    slugs: dict[str, str] = {}
    families: dict[str, str] = {}
    for plant in plants:
        if plant.slug in slugs:
            refuse(
                FINDING_DUPLICATE_SLUG,
                f"slug {shown(plant.slug)} repeats ({slugs[plant.slug]} and {plant.family})",
            )
        slugs[plant.slug] = plant.family
        if plant.family in families:
            refuse(FINDING_DUPLICATE_FAMILY, f"family {shown(plant.family)} repeats")
        families[plant.family] = plant.slug


def _plant_row(row: Mapping[str, Any], where: str) -> cat.Plant:
    extra = sorted(set(row) - set(cat.PLANT_FIELDS))
    refuse_when(bool(extra), FINDING_FIELD_INVALID, f"{where} extra {extra}")
    return cat.plant_from_mapping(row, where)


def _read_plants_jsonl(path: Path) -> tuple[cat.Plant, ...]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        refuse(FINDING_CATALOG_FILE_MISSING, f"{path} is unreadable: {exc}")
    refuse_when(
        "\r" in text or not text.endswith("\n"),
        FINDING_FIELD_INVALID,
        f"{path.name} must be LF-framed jsonl",
    )
    plants: list[cat.Plant] = []
    for index, line in enumerate(text.splitlines(), start=1):
        refuse_when(not line, FINDING_FIELD_INVALID, f"{path.name}:{index} is empty")
        refuse_when(
            line[:1] in {" ", "\t"},
            FINDING_FIELD_INVALID,
            f"{path.name}:{index} has leading whitespace",
        )
        try:
            row = load_strict_json(line)
        except ValueError as exc:
            refuse(FINDING_FIELD_INVALID, f"{path.name}:{index} is not strict JSON: {exc}")
        refuse_when(
            not isinstance(row, dict),
            FINDING_FIELD_INVALID,
            f"{path.name}:{index} must be an object",
        )
        plants.append(_plant_row(row, f"{path.name}:{index}"))
    return tuple(plants)


def _load_meta(directory: Path) -> tuple[dict[str, Any], bytes, str]:
    meta_path = directory / CATALOG_FILENAME
    plants_path = directory / PLANTS_FILENAME
    refuse_when(not meta_path.is_file(), FINDING_CATALOG_FILE_MISSING, f"missing {meta_path}")
    refuse_when(not plants_path.is_file(), FINDING_CATALOG_FILE_MISSING, f"missing {plants_path}")
    try:
        meta = load_strict_json(meta_path.read_text(encoding="utf-8"))
    except ValueError as exc:
        refuse(FINDING_FIELD_INVALID, f"{CATALOG_FILENAME} is not strict JSON: {exc}")
    refuse_when(not isinstance(meta, dict), FINDING_FIELD_INVALID, f"{CATALOG_FILENAME} must be an object")
    missing = [key for key in CATALOG_META_KEYS if key not in meta]
    refuse_when(bool(missing), FINDING_FIELD_MISSING, f"{CATALOG_FILENAME} missing {missing}")
    extra = sorted(set(meta) - set(CATALOG_META_KEYS))
    refuse_when(bool(extra), FINDING_FIELD_INVALID, f"{CATALOG_FILENAME} extra {extra}")
    refuse_when(
        meta.get("format") != CATALOG_FORMAT,
        FINDING_FIELD_INVALID,
        f"format {shown(meta.get('format'))} != {CATALOG_FORMAT}",
    )
    refuse_when(meta.get("factory") != FACTORY, FINDING_FIELD_INVALID, "factory pin mismatch")
    refuse_when(meta.get("catalog_id") != CATALOG_ID, FINDING_FIELD_INVALID, "catalog_id pin mismatch")
    plants_bytes = plants_path.read_bytes()
    digest = _sha256_bytes(plants_bytes)
    refuse_when(
        meta.get("plants_sha256") != digest,
        FINDING_PLANTS_SHA_MISMATCH,
        f"{PLANTS_FILENAME} sha256 {digest} != pinned {meta.get('plants_sha256')}",
    )
    return meta, plants_bytes, digest


def load_catalog(directory: Path | None = None) -> cat.Catalog:
    catalog_dir = Path(directory) if directory is not None else DEFAULT_CATALOG_DIR
    meta, _plants_bytes, _digest = _load_meta(catalog_dir)
    plants = _read_plants_jsonl(catalog_dir / PLANTS_FILENAME)
    refuse_when(not plants, FINDING_CATALOG_EMPTY, "r817 catalog has no plants")
    refuse_when(
        len(plants) != meta["plant_count"],
        FINDING_FIELD_INVALID,
        f"{PLANTS_FILENAME} has {len(plants)} rows; {CATALOG_FILENAME} says {meta['plant_count']}",
    )
    refuse_when(
        len(plants) % PLANTS_PER_ROUND != 0,
        FINDING_CATALOG_TRIPLE_STRIDE,
        f"r817 catalog length {len(plants)} is not a multiple of {PLANTS_PER_ROUND}",
    )
    _check_unique(plants)
    if catalog_dir.resolve() == DEFAULT_CATALOG_DIR.resolve():
        refuse_when(
            meta.get("source_commit") != SOURCE_COMMIT,
            FINDING_FIELD_INVALID,
            f"source_commit {shown(meta.get('source_commit'))} != {SOURCE_COMMIT}",
        )
        refuse_when(
            meta.get("source_sha256") != SOURCE_SHA256,
            FINDING_FIELD_INVALID,
            "source_sha256 pin drifted from r817.py",
        )
        refuse_when(
            meta.get("source_blob_sha1") != SOURCE_BLOB_SHA1,
            FINDING_FIELD_INVALID,
            "source_blob_sha1 pin drifted from r817.py",
        )
        refuse_when(
            meta.get("source_path") != SOURCE_PATH,
            FINDING_FIELD_INVALID,
            "source_path pin drifted from r817.py",
        )
        refuse_when(
            meta.get("source_method") != SOURCE_METHOD,
            FINDING_FIELD_INVALID,
            "source_method pin drifted from r817.py",
        )
        refuse_when(
            meta.get("source_lines") != SOURCE_LINES,
            FINDING_FIELD_INVALID,
            "source_lines pin drifted from r817.py",
        )
        refuse_when(
            meta.get("wave_first_round") != WAVE_FIRST_ROUND
            or meta.get("wave_last_round") != WAVE_LAST_ROUND,
            FINDING_FIELD_INVALID,
            "wave range pin drifted from r817.py",
        )
    return cat.Catalog(str(meta["catalog_id"]), plants)


def catalog_check(directory: Path | None = None) -> dict[str, Any]:
    """Fail closed unless every r817 row has noun, unique identity, and a 3-stride."""

    loaded = load_catalog(directory)
    items = loaded.plants
    for plant in items:
        refuse_when(not plant.noun, FINDING_NOUN_MISSING, f"{plant.slug} is missing noun")
        refuse_when(
            plant.repo != f"plant/{plant.noun}-{plant.slug}",
            FINDING_FIELD_INVALID,
            f"{plant.slug} repo drifted from noun",
        )
    return {
        "status": "ok",
        "catalog_id": loaded.catalog_id,
        "plants": len(items),
        "triples": len(items) // PLANTS_PER_ROUND,
        "nouns": len({plant.noun for plant in items}),
        "first_round": WAVE_FIRST_ROUND,
        "last_round": WAVE_FIRST_ROUND + len(items) // PLANTS_PER_ROUND - 1,
    }


def plants_for_round(round_n: int, plants: tuple[cat.Plant, ...] | None = None) -> tuple[cat.Plant, ...]:
    items = load_catalog().plants if plants is None else plants
    last = WAVE_FIRST_ROUND + len(items) // PLANTS_PER_ROUND - 1
    refuse_first((
        (type(round_n) is not int, FINDING_ROUND_OUT_OF_DOMAIN,
         f"round must be an int, got {shown(round_n)}"),
        (type(round_n) is int and not WAVE_FIRST_ROUND <= round_n <= last,
         FINDING_ROUND_OUT_OF_DOMAIN,
         f"round must lie in [{WAVE_FIRST_ROUND}, {last}], got {shown(round_n)}"),
    ))
    start = (round_n - WAVE_FIRST_ROUND) * PLANTS_PER_ROUND
    chunk = items[start:start + PLANTS_PER_ROUND]
    refuse_when(
        len(chunk) != PLANTS_PER_ROUND,
        FINDING_TRIPLE_OUT_OF_DOMAIN,
        f"no plant triple for r{round_n}",
    )
    return chunk


_CATALOG = load_catalog()

bind_import_twin(__name__)
