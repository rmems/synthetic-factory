"""Shared loader and validator for pinned CRP wave catalogs.

Wave modules intentionally keep their pins as module constants.  They build a
fresh :class:`WaveSpec` at each public call so tests and downstream tooling can
temporarily redirect a wrapper's catalog directory without affecting another
wave.
"""

from __future__ import annotations

import hashlib
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
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

CATALOG_META_KEYS = (
    "catalog_id", "extraction", "family", "factory", "format", "generator",
    "intended_use", "plant_count", "plants_filename", "plants_sha256",
    "project_training_policy", "quota_per_round", "record_kind", "slice",
    "source_blob_sha1", "source_commit", "source_lines", "source_method",
    "source_path", "source_ref", "source_sha256", "wave_first_round",
    "wave_last_round",
)


@dataclass(frozen=True)
class WaveSpec:
    """Immutable pins and paths that distinguish one catalog wave."""

    name: str
    catalog_id: str
    catalog_format: str
    catalog_filename: str
    plants_filename: str
    wave_first_round: int
    wave_last_round: int
    source_ref: str
    source_commit: str
    source_path: str
    source_method: str
    source_blob_sha1: str
    source_sha256: str
    source_lines: int
    default_catalog_dir: Path


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def git_show_source(spec: WaveSpec, path: str) -> str:
    """Return pinned mill source via ``git show``; never import or execute it."""

    tried: list[str] = []
    for ref in (f"origin/{spec.source_ref}", spec.source_commit, spec.source_ref):
        source_spec = f"{ref}:{path}"
        tried.append(source_spec)
        proc = subprocess.run(
            ["git", "show", source_spec], cwd=repo_root(), capture_output=True, check=False
        )
        if proc.returncode != 0:
            continue
        digest = _sha256_bytes(proc.stdout)
        refuse_when(
            digest != spec.source_sha256,
            FINDING_AST_NOT_A_PLANT,
            f"{source_spec} sha256 {digest} != pinned {spec.source_sha256}",
        )
        return proc.stdout.decode("utf-8")
    refuse(
        FINDING_AST_NOT_A_PLANT,
        f"{spec.source_ref} pin is not fetchable ({', '.join(tried)})",
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


def _load_meta(spec: WaveSpec, directory: Path) -> dict[str, Any]:
    meta_path = directory / spec.catalog_filename
    plants_path = directory / spec.plants_filename
    refuse_when(not meta_path.is_file(), FINDING_CATALOG_FILE_MISSING, f"missing {meta_path}")
    refuse_when(not plants_path.is_file(), FINDING_CATALOG_FILE_MISSING, f"missing {plants_path}")
    try:
        meta = load_strict_json(meta_path.read_text(encoding="utf-8"))
    except ValueError as exc:
        refuse(FINDING_FIELD_INVALID, f"{spec.catalog_filename} is not strict JSON: {exc}")
    refuse_when(not isinstance(meta, dict), FINDING_FIELD_INVALID, "CATALOG.json must be an object")
    missing = [key for key in CATALOG_META_KEYS if key not in meta]
    refuse_when(bool(missing), FINDING_FIELD_MISSING, f"CATALOG.json missing {missing}")
    extra = sorted(set(meta) - set(CATALOG_META_KEYS))
    refuse_when(bool(extra), FINDING_FIELD_INVALID, f"CATALOG.json extra {extra}")
    refuse_when(meta.get("format") != spec.catalog_format, FINDING_FIELD_INVALID,
                f"format {shown(meta.get('format'))} != {spec.catalog_format}")
    refuse_when(meta.get("factory") != cat.FACTORY, FINDING_FIELD_INVALID, "factory pin mismatch")
    refuse_when(meta.get("catalog_id") != spec.catalog_id, FINDING_FIELD_INVALID,
                "catalog_id pin mismatch")
    digest = _sha256_bytes(plants_path.read_bytes())
    refuse_when(meta.get("plants_sha256") != digest, FINDING_PLANTS_SHA_MISMATCH,
                f"{spec.plants_filename} sha256 {digest} != pinned {meta.get('plants_sha256')}")
    return meta


def load_catalog(spec: WaveSpec, directory: Path | None = None) -> cat.Catalog:
    catalog_dir = Path(directory) if directory is not None else spec.default_catalog_dir
    meta = _load_meta(spec, catalog_dir)
    plants = _read_plants_jsonl(catalog_dir / spec.plants_filename)
    refuse_when(not plants, FINDING_CATALOG_EMPTY, f"{spec.name} catalog has no plants")
    refuse_when(len(plants) != meta["plant_count"], FINDING_FIELD_INVALID,
                f"{spec.plants_filename} has {len(plants)} rows; CATALOG.json says {meta['plant_count']}")
    refuse_when(len(plants) % cat.PLANTS_PER_ROUND != 0, FINDING_CATALOG_TRIPLE_STRIDE,
                f"{spec.name} catalog length {len(plants)} is not a multiple of {cat.PLANTS_PER_ROUND}")
    _check_unique(plants)
    if catalog_dir.resolve() == spec.default_catalog_dir.resolve():
        pins = {
            "source_commit": spec.source_commit,
            "source_sha256": spec.source_sha256,
            "source_blob_sha1": spec.source_blob_sha1,
            "source_path": spec.source_path,
            "source_method": spec.source_method,
            "source_lines": spec.source_lines,
        }
        for field, expected in pins.items():
            refuse_when(meta.get(field) != expected, FINDING_FIELD_INVALID,
                        f"{field} pin drifted from {spec.name}.py")
        refuse_when(
            meta.get("wave_first_round") != spec.wave_first_round
            or meta.get("wave_last_round") != spec.wave_last_round,
            FINDING_FIELD_INVALID,
            f"wave range pin drifted from {spec.name}.py",
        )
    return cat.Catalog(str(meta["catalog_id"]), plants)


def catalog_check(spec: WaveSpec, directory: Path | None = None) -> dict[str, Any]:
    loaded = load_catalog(spec, directory)
    items = loaded.plants
    for plant in items:
        refuse_when(not plant.noun, FINDING_NOUN_MISSING, f"{plant.slug} is missing noun")
        refuse_when(plant.repo != f"plant/{plant.noun}-{plant.slug}", FINDING_FIELD_INVALID,
                    f"{plant.slug} repo drifted from noun")
    return {
        "status": "ok", "catalog_id": loaded.catalog_id, "plants": len(items),
        "triples": len(items) // cat.PLANTS_PER_ROUND,
        "nouns": len({plant.noun for plant in items}),
        "first_round": spec.wave_first_round,
        "last_round": spec.wave_first_round + len(items) // cat.PLANTS_PER_ROUND - 1,
    }


def plants_for_round(
    spec: WaveSpec,
    round_n: int,
    plants: tuple[cat.Plant, ...] | None = None,
) -> tuple[cat.Plant, ...]:
    items = load_catalog(spec).plants if plants is None else plants
    last = spec.wave_first_round + len(items) // cat.PLANTS_PER_ROUND - 1
    refuse_first((
        (type(round_n) is not int, FINDING_ROUND_OUT_OF_DOMAIN,
         f"round must be an int, got {shown(round_n)}"),
        (type(round_n) is int and not spec.wave_first_round <= round_n <= last,
         FINDING_ROUND_OUT_OF_DOMAIN,
         f"round must lie in [{spec.wave_first_round}, {last}], got {shown(round_n)}"),
    ))
    start = (round_n - spec.wave_first_round) * cat.PLANTS_PER_ROUND
    chunk = items[start:start + cat.PLANTS_PER_ROUND]
    refuse_when(len(chunk) != cat.PLANTS_PER_ROUND, FINDING_TRIPLE_OUT_OF_DOMAIN,
                f"no plant triple for r{round_n}")
    return chunk


bind_import_twin(__name__)
