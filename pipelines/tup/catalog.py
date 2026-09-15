#!/usr/bin/env python3
"""Pinned TUP r1349 family catalog: AST extract, expand, load, uniqueness.

``config/tup/families.jsonl`` holds the 138 ``extra_catalog`` families from
``experiments/tup-mill-r1349.py``. Expansion matches that mill's ``add()``
(slug ``{bin}-{short}``, inspect-vs-destroy, wait ``3 + i % 5``). Load
raises at catalog boundaries rather than excluding per row.
"""

from __future__ import annotations

import ast
import hashlib
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from ._contract import (
    CATALOG_FILENAME,
    CATALOG_FORMAT,
    DEFAULT_CATALOG_ID,
    FACTORY,
    FAMILIES_FILENAME,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_PLANT_DUPLICATE,
    FINDING_PLANT_FIELD_INVALID,
    FINDING_PLANT_FIELD_MISSING,
    FINDING_PLANT_NOT_FOUND,
    FINDING_PLANTS_SHA_MISMATCH,
    FINDING_SOURCE_NOT_PARSEABLE,
    GENERATOR,
    SOURCE_COMMIT,
    SOURCE_PATH,
    SOURCE_REF,
    SOURCE_SHA256,
    bind_import_twin,
    load_strict_json,
    refuse,
    refuse_when,
    repo_root,
)

DEFAULT_CATALOG_DIR = Path(__file__).resolve().parents[2] / "config" / "tup"

CATALOG_META_KEYS = (
    "banned_bits",
    "banned_goal",
    "banned_prefix",
    "banned_slugs",
    "catalog_id",
    "factory",
    "families",
    "families_filename",
    "families_sha256",
    "family",
    "generator",
    "intended_use",
    "plants",
    "project_training_policy",
    "quota_per_round",
    "schema",
    "sins",
    "slice",
    "source_blob_sha1",
    "source_commit",
    "source_lines",
    "source_method",
    "source_path",
    "source_ref",
    "source_sha256",
)
FAMILY_KEYS = ("bin", "cmds", "grep", "keep")

__all__ = [
    "CATALOG_META_KEYS",
    "Catalog",
    "DEFAULT_CATALOG_DIR",
    "Family",
    "Plant",
    "catalog_check",
    "default_catalog_dir",
    "expand_families",
    "families_from_source",
    "git_show_source",
    "load_catalog",
]


def default_catalog_dir() -> Path:
    return DEFAULT_CATALOG_DIR


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _as_str(value: Any, label: str) -> str:
    refuse_when(
        not isinstance(value, str) or not value,
        FINDING_PLANT_FIELD_INVALID,
        f"{label} must be a non-empty string",
    )
    return value


def _as_int(value: Any, label: str) -> int:
    refuse_when(
        not isinstance(value, int) or isinstance(value, bool),
        FINDING_PLANT_FIELD_INVALID,
        f"{label} must be an int, got {type(value).__name__}",
    )
    return value


def _as_str_tuple(value: Any, label: str) -> tuple[str, ...]:
    refuse_when(
        not isinstance(value, list),
        FINDING_CATALOG_FIELD_INVALID,
        f"{label} must be a list",
    )
    return tuple(_as_str(item, f"{label}[{index}]") for index, item in enumerate(value))


@dataclass(frozen=True)
class Family:
    bin: str
    keep: str
    grep: str
    cmds: tuple[tuple[str, str, str], ...]


@dataclass(frozen=True)
class Plant:
    slug: str
    bin: str
    verify: str
    destroy: str
    keep: str
    wait: int
    grep: str

    @property
    def plant_id(self) -> str:
        return f"{SLICE_MILL}:{self.slug}"


SLICE_MILL = "tup_r1349"


@dataclass(frozen=True)
class Catalog:
    directory: Path
    meta: Mapping[str, Any]
    families_sha256: str
    families: tuple[Family, ...]
    plants: tuple[Plant, ...]

    @property
    def catalog_id(self) -> str:
        return str(self.meta["catalog_id"])

    @property
    def factory(self) -> str:
        return str(self.meta["factory"])

    def plant(self, plant_id: str) -> Plant:
        for row in self.plants:
            if row.plant_id == plant_id or row.slug == plant_id:
                return row
        refuse(FINDING_PLANT_NOT_FOUND, f"no tup plant {plant_id!r}")


def _literal_str(node: ast.AST, label: str) -> str:
    refuse_when(
        not isinstance(node, ast.Constant) or not isinstance(node.value, str) or not node.value,
        FINDING_SOURCE_NOT_PARSEABLE,
        f"{label} is not a non-empty string literal",
    )
    return node.value


def _cmd_row(node: ast.AST, label: str) -> tuple[str, str, str]:
    refuse_when(
        not isinstance(node, (ast.List, ast.Tuple)) or len(node.elts) != 3,
        FINDING_SOURCE_NOT_PARSEABLE,
        f"{label} is not a 3-tuple",
    )
    return (
        _literal_str(node.elts[0], f"{label}.short"),
        _literal_str(node.elts[1], f"{label}.verify"),
        _literal_str(node.elts[2], f"{label}.destroy"),
    )


def families_from_source(source: str) -> tuple[Family, ...]:
    """AST-extract ``extra_catalog`` families. Never ``exec`` the mill."""

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        refuse(FINDING_SOURCE_NOT_PARSEABLE, f"mill source is not parseable: {exc}")
    extra = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "extra_catalog"
        ),
        None,
    )
    refuse_when(extra is None, FINDING_SOURCE_NOT_PARSEABLE, "missing extra_catalog")
    assign = next(
        (
            node
            for node in extra.body
            if isinstance(node, ast.Assign)
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "families"
        ),
        None,
    )
    refuse_when(
        assign is None or not isinstance(assign.value, (ast.List, ast.Tuple)),
        FINDING_SOURCE_NOT_PARSEABLE,
        "missing families list",
    )
    families: list[Family] = []
    for index, elt in enumerate(assign.value.elts):
        label = f"families[{index}]"
        refuse_when(
            not isinstance(elt, (ast.List, ast.Tuple)) or len(elt.elts) != 4,
            FINDING_SOURCE_NOT_PARSEABLE,
            f"{label} is not a 4-tuple",
        )
        cmds_node = elt.elts[3]
        refuse_when(
            not isinstance(cmds_node, (ast.List, ast.Tuple)) or not cmds_node.elts,
            FINDING_SOURCE_NOT_PARSEABLE,
            f"{label}.cmds is empty",
        )
        families.append(
            Family(
                bin=_literal_str(elt.elts[0], f"{label}.bin"),
                keep=_literal_str(elt.elts[1], f"{label}.keep"),
                grep=_literal_str(elt.elts[2], f"{label}.grep"),
                cmds=tuple(
                    _cmd_row(cmd, f"{label}.cmds[{i}]")
                    for i, cmd in enumerate(cmds_node.elts)
                ),
            )
        )
    refuse_when(not families, FINDING_SOURCE_NOT_PARSEABLE, "extra_catalog families is empty")
    return tuple(families)


def expand_families(
    families: Sequence[Family],
    *,
    banned_slugs: Sequence[str],
    banned_prefix: Sequence[str],
) -> tuple[Plant, ...]:
    """Replay r1349 ``add()`` without importing ``tup_mill``."""

    banned = frozenset(banned_slugs)
    prefixes = tuple(banned_prefix)
    plants: list[Plant] = []
    index = 0
    for family in families:
        for short, verify_args, destroy in family.cmds:
            slug = f"{family.bin}-{short}"
            if slug in banned or any(slug.startswith(prefix) for prefix in prefixes):
                continue
            if slug.startswith("yq-eval") or slug.startswith("pacman"):
                continue
            verify = f"{family.bin} {verify_args}".strip()
            dest = destroy if destroy.startswith(("rm ", family.bin)) else f"{family.bin} {destroy}"
            plants.append(
                Plant(
                    slug=slug,
                    bin=family.bin.split()[0],
                    verify=verify,
                    destroy=dest,
                    keep=family.keep,
                    wait=3 + (index % 5),
                    grep=family.grep,
                )
            )
            index += 1
    return tuple(plants)


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
            FINDING_SOURCE_NOT_PARSEABLE,
            f"{spec} sha256 {digest} != pinned {SOURCE_SHA256}",
        )
        return proc.stdout.decode("utf-8")
    refuse(
        FINDING_SOURCE_NOT_PARSEABLE,
        f"legacy-mill-lane pin is not fetchable ({', '.join(tried)})",
    )


def _family_from_row(row: Mapping[str, Any], lineno: int) -> Family:
    missing = [key for key in FAMILY_KEYS if key not in row]
    refuse_when(bool(missing), FINDING_PLANT_FIELD_MISSING, f"line {lineno} missing {missing}")
    extra = sorted(set(row) - set(FAMILY_KEYS))
    refuse_when(bool(extra), FINDING_PLANT_FIELD_INVALID, f"line {lineno} extra {extra}")
    cmds_raw = row["cmds"]
    refuse_when(
        not isinstance(cmds_raw, list) or not cmds_raw,
        FINDING_PLANT_FIELD_INVALID,
        f"line {lineno} cmds",
    )
    cmds: list[tuple[str, str, str]] = []
    for index, item in enumerate(cmds_raw):
        refuse_when(
            not isinstance(item, list) or len(item) != 3,
            FINDING_PLANT_FIELD_INVALID,
            f"line {lineno} cmds[{index}] is not a 3-list",
        )
        cmds.append(
            (
                _as_str(item[0], f"line {lineno} cmds[{index}].short"),
                _as_str(item[1], f"line {lineno} cmds[{index}].verify"),
                _as_str(item[2], f"line {lineno} cmds[{index}].destroy"),
            )
        )
    return Family(
        bin=_as_str(row["bin"], f"line {lineno} bin"),
        keep=_as_str(row["keep"], f"line {lineno} keep"),
        grep=_as_str(row["grep"], f"line {lineno} grep"),
        cmds=tuple(cmds),
    )


def _load_meta(directory: Path) -> tuple[dict[str, Any], bytes, str]:
    meta_path = directory / CATALOG_FILENAME
    families_path = directory / FAMILIES_FILENAME
    refuse_when(not meta_path.is_file(), FINDING_CATALOG_FILE_MISSING, f"missing {meta_path}")
    refuse_when(
        not families_path.is_file(),
        FINDING_CATALOG_FILE_MISSING,
        f"missing {families_path}",
    )
    meta = load_strict_json(meta_path.read_text(encoding="utf-8"))
    refuse_when(
        not isinstance(meta, dict),
        FINDING_CATALOG_FIELD_INVALID,
        "CATALOG.json must be an object",
    )
    missing = [key for key in CATALOG_META_KEYS if key not in meta]
    refuse_when(bool(missing), FINDING_CATALOG_FIELD_MISSING, f"CATALOG.json missing {missing}")
    refuse_when(
        meta.get("schema") != CATALOG_FORMAT,
        FINDING_CATALOG_FIELD_INVALID,
        f"schema {meta.get('schema')!r} != {CATALOG_FORMAT}",
    )
    refuse_when(
        meta.get("factory") != FACTORY,
        FINDING_CATALOG_FIELD_INVALID,
        "factory pin mismatch",
    )
    refuse_when(
        meta.get("generator") != GENERATOR,
        FINDING_CATALOG_FIELD_INVALID,
        "generator pin mismatch",
    )
    refuse_when(
        meta.get("catalog_id") != DEFAULT_CATALOG_ID and directory == DEFAULT_CATALOG_DIR,
        FINDING_CATALOG_FIELD_INVALID,
        f"catalog_id {meta.get('catalog_id')!r} != {DEFAULT_CATALOG_ID}",
    )
    families_bytes = families_path.read_bytes()
    digest = _sha256_bytes(families_bytes)
    refuse_when(
        meta.get("families_sha256") != digest,
        FINDING_PLANTS_SHA_MISMATCH,
        f"families.jsonl sha256 {digest} != pinned {meta.get('families_sha256')}",
    )
    return meta, families_bytes, digest


def load_catalog(directory: Path | None = None) -> Catalog:
    catalog_dir = Path(directory) if directory is not None else DEFAULT_CATALOG_DIR
    meta, families_bytes, digest = _load_meta(catalog_dir)
    families = tuple(
        _family_from_row(load_strict_json(line), lineno)
        for lineno, line in enumerate(families_bytes.decode("utf-8").splitlines(), start=1)
        if line
    )
    refuse_when(
        len(families) != meta["families"],
        FINDING_CATALOG_FIELD_INVALID,
        f"families.jsonl has {len(families)} rows; CATALOG.json says {meta['families']}",
    )
    plants = expand_families(
        families,
        banned_slugs=_as_str_tuple(meta["banned_slugs"], "banned_slugs"),
        banned_prefix=_as_str_tuple(meta["banned_prefix"], "banned_prefix"),
    )
    refuse_when(
        len(plants) != meta["plants"],
        FINDING_CATALOG_FIELD_INVALID,
        f"expanded {len(plants)} plants; CATALOG.json says {meta['plants']}",
    )
    slugs = [plant.slug for plant in plants]
    refuse_when(
        len(set(slugs)) != len(slugs),
        FINDING_PLANT_DUPLICATE,
        "duplicate slugs in tup catalog",
    )
    if catalog_dir.resolve() == DEFAULT_CATALOG_DIR.resolve():
        refuse_when(
            meta.get("source_commit") != SOURCE_COMMIT,
            FINDING_CATALOG_FIELD_INVALID,
            f"source_commit {meta.get('source_commit')!r} != {SOURCE_COMMIT}",
        )
    return Catalog(
        directory=catalog_dir,
        meta=MappingProxyType(dict(meta)),
        families_sha256=digest,
        families=families,
        plants=plants,
    )


def catalog_check(directory: Path | None = None) -> list[str]:
    loaded = load_catalog(directory)
    findings: list[str] = []
    if loaded.meta.get("source_sha256") != SOURCE_SHA256:
        findings.append("source_sha256 pin drifted from _contract")
    if loaded.meta.get("source_path") != SOURCE_PATH:
        findings.append("source_path pin drifted from _contract")
    return findings


_CATALOG = load_catalog()

bind_import_twin(__name__)
