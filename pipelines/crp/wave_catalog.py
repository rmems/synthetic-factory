"""Shared loader and validator for pinned CRP wave catalogs.

Wave modules keep a short lane-owned docstring and call :func:`install_wave`
so pins, public callables, and the import twin stay consistent across waves.
Each public call rebuilds a :class:`WaveSpec` from the wrapper's live globals
so tests can redirect ``DEFAULT_CATALOG_DIR`` on one wave without affecting
another.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess  # nosec B404 — git show of pinned mill source only
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



_SOURCE_METHOD = 'git-show+ast.parse'
_SOURCE_REF = 'legacy-mill-lane'
_WAVE_PIN_FIELDS = (
    'CATALOG_ID',
    'CATALOG_FORMAT',
    'CATALOG_FILENAME',
    'PLANTS_FILENAME',
    'WAVE_FIRST_ROUND',
    'EXPECTED_PLANTS',
    'RUN_FORMAT',
    'SOURCE_REF',
    'SOURCE_COMMIT',
    'SOURCE_PATH',
    'SOURCE_METHOD',
    'SOURCE_BLOB_SHA1',
    'SOURCE_SHA256',
    'SOURCE_LINES',
)
_WAVE_PIN_ROWS: tuple[tuple[object, ...], ...] = (
    ('r432', 'crp-r432-v1', 'crp-r432-catalog/1', 'CATALOG.json', 'plants.jsonl', 432, 366, 'crp-r432-run/1', _SOURCE_REF, '9237367ce58fb8d472e5fbc18e5dbffff35bca76', 'experiments/crp-mill-r432.py', _SOURCE_METHOD, '5d786849a4cd323e860f4d69708a13039e78c03e', '35fb74a24aa9ba08d77a977c5400734b036a7527c344055859c94c674b9b32b2', 3029),
    ('r538', 'crp-r538-v1', 'crp-r538-catalog/1', 'CATALOG-r538.json', 'plants-r538.jsonl', 538, 495, 'crp-r538-run/1', _SOURCE_REF, '813f93f1969c1c4421e5663492e9663739efa642', 'experiments/crp-mill-r538.py', _SOURCE_METHOD, 'b46e07318769c9ca0359f4cadee1ea9d65775c3c', '6b597a5c62f6b5f0738f5cd46ea8b09c05bc8ce32fc5ab8f7d40ea0cdb1f32d3', 3653),
    ('r729', 'crp-r729-v1', 'crp-r729-catalog/1', 'CATALOG-r729.json', 'plants-r729.jsonl', 729, 216, 'crp-r729-run/1', _SOURCE_REF, '813f93f1969c1c4421e5663492e9663739efa642', 'experiments/crp-mill-r729.py', _SOURCE_METHOD, '0be2c17f6ca22b0a773589380fe4d86299fdb35f', '1a090e78cc23f04ba93be3d49518260e1de9480cdf87d65e07dffbdfe64148d1', 1505),
    ('r817', 'crp-r817-v1', 'crp-r817-catalog/1', 'CATALOG-r817.json', 'plants-r817.jsonl', 817, 534, 'crp-r817-run/1', _SOURCE_REF, '813f93f1969c1c4421e5663492e9663739efa642', 'experiments/crp-mill-r817.py', _SOURCE_METHOD, 'ce27c89f7799e5508a3e8d8e2f068da972285aaf', 'b3da74de1071c0c5dd472c7fb0c5de42de5a2a9ccd11a62ef9204f108e51e616', 3429),
    ('r995', 'crp-r995-v1', 'crp-r995-catalog/1', 'CATALOG-r995.json', 'plants-r995.jsonl', 995, 1968, 'crp-r995-run/1', _SOURCE_REF, '813f93f1969c1c4421e5663492e9663739efa642', 'experiments/crp-mill-r995.py', _SOURCE_METHOD, '4f0c1788e877509c8f02f5540052806527f8644a', '7782322263f86b0934bb9955dfecd74e6ef068f147f99bb9bf8f74b5fef8efde', 12029),
    ('leftover3_prior', 'crp-leftover3-prior-v1', 'crp-leftover3-prior-catalog/1', 'CATALOG-leftover3-prior.json', 'plants-leftover3-prior.jsonl', 679, 48, 'crp-leftover3-prior-run/1', _SOURCE_REF, '813f93f1969c1c4421e5663492e9663739efa642', 'experiments/crp-mill-leftover3.py', _SOURCE_METHOD, '257941ca424fddb16608fe1a9eec0f4029a62857', 'eaa3867b23fdc726d55e2c347e00fed9b234d9cb51dc9667db2ed170149441c2', 466),
)

WAVE_PINS: dict[str, dict[str, object]] = {
    str(row[0]): {
        field: row[i + 1]
        for i, field in enumerate(_WAVE_PIN_FIELDS)
    }
    for row in _WAVE_PIN_ROWS
}


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
    expected_plants: int
    source_ref: str
    source_commit: str
    source_path: str
    source_method: str
    source_blob_sha1: str
    source_sha256: str
    source_lines: int
    default_catalog_dir: Path


_WAVE_EXPORTS = (
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
)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _git_executable() -> str:
    found = shutil.which("git")
    refuse_when(found is None, FINDING_AST_NOT_A_PLANT, "git executable not found on PATH")
    return found


def git_show_source(spec: WaveSpec, path: str) -> str:
    """Return pinned mill source via ``git show``; never import or execute it."""

    tried: list[str] = []
    git = _git_executable()
    for ref in (f"origin/{spec.source_ref}", spec.source_commit, spec.source_ref):
        source_spec = f"{ref}:{path}"
        tried.append(source_spec)
        proc = subprocess.run(  # nosec B603 — literal argv: git show <pinned-ref:path>
            [git, "show", source_spec],
            cwd=repo_root(),
            capture_output=True,
            check=False,
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


def _read_plants_jsonl(path_name: str, payload: bytes) -> tuple[cat.Plant, ...]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        refuse(FINDING_FIELD_INVALID, f"{path_name} is not utf-8: {exc}")
    refuse_when(
        "\r" in text or not text.endswith("\n"),
        FINDING_FIELD_INVALID,
        f"{path_name} must be LF-framed jsonl",
    )
    plants: list[cat.Plant] = []
    for index, line in enumerate(text.splitlines(), start=1):
        refuse_when(not line, FINDING_FIELD_INVALID, f"{path_name}:{index} is empty")
        refuse_when(
            line[:1] in {" ", "\t"},
            FINDING_FIELD_INVALID,
            f"{path_name}:{index} has leading whitespace",
        )
        try:
            row = load_strict_json(line)
        except ValueError as exc:
            refuse(FINDING_FIELD_INVALID, f"{path_name}:{index} is not strict JSON: {exc}")
        refuse_when(
            not isinstance(row, dict),
            FINDING_FIELD_INVALID,
            f"{path_name}:{index} must be an object",
        )
        plants.append(_plant_row(row, f"{path_name}:{index}"))
    return tuple(plants)


def _load_meta(spec: WaveSpec, directory: Path) -> tuple[dict[str, Any], bytes]:
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
    plants_bytes = plants_path.read_bytes()
    digest = _sha256_bytes(plants_bytes)
    refuse_when(meta.get("plants_sha256") != digest, FINDING_PLANTS_SHA_MISMATCH,
                f"{spec.plants_filename} sha256 {digest} != pinned {meta.get('plants_sha256')}")
    return meta, plants_bytes


def load_catalog(spec: WaveSpec, directory: Path | None = None) -> cat.Catalog:
    catalog_dir = Path(directory) if directory is not None else spec.default_catalog_dir
    meta, plants_bytes = _load_meta(spec, catalog_dir)
    plants = _read_plants_jsonl(spec.plants_filename, plants_bytes)
    refuse_when(not plants, FINDING_CATALOG_EMPTY, f"{spec.name} catalog has no plants")
    refuse_when(len(plants) != meta["plant_count"], FINDING_FIELD_INVALID,
                f"{spec.plants_filename} has {len(plants)} rows; CATALOG.json says {meta['plant_count']}")
    refuse_when(
        len(plants) != spec.expected_plants,
        FINDING_FIELD_INVALID,
        f"{spec.plants_filename} has {len(plants)} rows; {spec.name}.py EXPECTED_PLANTS is {spec.expected_plants}",
    )
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
        "last_round": spec.wave_last_round,
    }


def plants_for_round(
    spec: WaveSpec,
    round_n: int,
    plants: tuple[cat.Plant, ...] | None = None,
) -> tuple[cat.Plant, ...]:
    items = load_catalog(spec).plants if plants is None else plants
    last = spec.wave_last_round
    # type() — not isinstance — so bool is refused (bool subclasses int).
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


def spec_from_module(ns: dict[str, Any]) -> WaveSpec:
    return WaveSpec(
        name=ns["__name__"].rsplit(".", 1)[-1],
        catalog_id=ns["CATALOG_ID"],
        catalog_format=ns["CATALOG_FORMAT"],
        catalog_filename=ns["CATALOG_FILENAME"],
        plants_filename=ns["PLANTS_FILENAME"],
        wave_first_round=ns["WAVE_FIRST_ROUND"],
        wave_last_round=ns["WAVE_LAST_ROUND"],
        expected_plants=ns["EXPECTED_PLANTS"],
        source_ref=ns["SOURCE_REF"],
        source_commit=ns["SOURCE_COMMIT"],
        source_path=ns["SOURCE_PATH"],
        source_method=ns["SOURCE_METHOD"],
        source_blob_sha1=ns["SOURCE_BLOB_SHA1"],
        source_sha256=ns["SOURCE_SHA256"],
        source_lines=ns["SOURCE_LINES"],
        default_catalog_dir=ns["DEFAULT_CATALOG_DIR"],
    )


def install_wave(ns: dict[str, Any]) -> None:
    """Materialize pins and shared loader callables onto a wave module."""

    wave = Path(ns["__file__"]).stem
    refuse_when(wave not in WAVE_PINS, FINDING_FIELD_INVALID, f"unknown CRP wave {wave!r}")
    pin = WAVE_PINS[wave]
    ns.update(pin)
    ns["FACTORY"] = cat.FACTORY
    ns["GENERATOR"] = cat.GENERATOR
    ns["ID_PREFIX"] = cat.ID_PREFIX
    ns["PLANTS_PER_ROUND"] = cat.PLANTS_PER_ROUND
    ns["WAVE_LAST_ROUND"] = (
        pin["WAVE_FIRST_ROUND"] + (pin["EXPECTED_PLANTS"] // cat.PLANTS_PER_ROUND) - 1
    )
    ns["DEFAULT_CATALOG_DIR"] = Path(ns["__file__"]).resolve().parents[2] / "config" / "crp"
    ns["CATALOG_META_KEYS"] = CATALOG_META_KEYS

    show = git_show_source
    load = load_catalog
    check = catalog_check
    for_round = plants_for_round

    def _spec() -> WaveSpec:
        return spec_from_module(ns)

    def default_catalog_dir() -> Path:
        return ns["DEFAULT_CATALOG_DIR"]

    def git_show_source_fn(path: str | None = None) -> str:
        """Return mill source via ``git show``. Never import or execute the mill."""
        spec = _spec()
        return show(spec, spec.source_path if path is None else path)

    def load_catalog_fn(directory: Path | None = None) -> cat.Catalog:
        return load(_spec(), directory)

    def catalog_check_fn(directory: Path | None = None) -> dict[str, Any]:
        """Fail closed unless every row has noun, unique identity, and a 3-stride."""
        return check(_spec(), directory)

    def plants_for_round_fn(
        round_n: int,
        plants_arg: tuple[cat.Plant, ...] | None = None,
    ) -> tuple[cat.Plant, ...]:
        return for_round(_spec(), round_n, plants_arg)

    ns["__all__"] = list(_WAVE_EXPORTS)
    ns["default_catalog_dir"] = default_catalog_dir
    ns["git_show_source"] = git_show_source_fn
    ns["load_catalog"] = load_catalog_fn
    ns["catalog_check"] = catalog_check_fn
    ns["plants_for_round"] = plants_for_round_fn
    ns["_CATALOG"] = load_catalog_fn()


bind_import_twin(__name__)
