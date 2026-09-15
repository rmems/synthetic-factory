#!/usr/bin/env python3
"""Load and pin-check a mill plant catalog. Never imports leftover mill scripts."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from . import catalog as cat
from . import vocabulary as cv
from ._contract import bind_import_twin, load_strict_json

__all__ = ["DEFAULT_CATALOG", "load_catalog", "sha256_bytes"]

_REPO = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = _REPO / "catalogs" / "mill"
_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_STEM = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)+$")
_HTTPS = re.compile(r"^https://[^\s]+$")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _read(path: Path, code: str) -> bytes:
    cv.refuse_when(not path.is_file(), code, f"missing catalog file {path.name}")
    return path.read_bytes()


def _require_str(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    cv.refuse_when(
        not isinstance(value, str) or not value.strip(),
        cv.FINDING_PLANT_FIELD_MISSING,
        f"plant field {key} must be a nonempty string",
    )
    return value


def _refuse_banned_text(text: str, where: str) -> None:
    for banned in cv.BANNED_SUBSTRINGS:
        cv.refuse_when(
            banned in text,
            cv.FINDING_BANNED_SUBSTRING,
            f"{where} carries banned substring {banned!r}",
        )


def _plant_from_row(row: Any, index: int) -> cat.Plant:
    cv.refuse_when(
        not isinstance(row, dict),
        cv.FINDING_INPUT_NOT_AN_OBJECT,
        f"plants.jsonl line {index} is not an object",
    )
    missing = [key for key in cat.PLANT_KEYS if key not in row]
    cv.refuse_when(
        bool(missing),
        cv.FINDING_PLANT_FIELD_MISSING,
        f"plants.jsonl line {index} missing {missing}",
    )
    extra = [key for key in row if key not in cat.PLANT_KEYS]
    cv.refuse_when(
        bool(extra),
        cv.FINDING_PLANT_FIELD_INVALID,
        f"plants.jsonl line {index} has unknown keys {extra}",
    )
    docs = row["docs"]
    cv.refuse_when(
        not isinstance(docs, list) or len(docs) != 2,
        cv.FINDING_PLANT_FIELD_INVALID,
        f"plants.jsonl line {index} docs must be two https URLs",
    )
    strings = {key: _require_str(row, key) for key in cat.PLANT_KEYS if key != "docs"}
    for key, value in strings.items():
        _refuse_banned_text(value, f"plant {strings['plant_id']} field {key}")
    for url in docs:
        cv.refuse_when(
            not isinstance(url, str) or not _HTTPS.match(url),
            cv.FINDING_PLANT_FIELD_INVALID,
            f"plant {strings['plant_id']} docs must be https URLs",
        )
        _refuse_banned_text(url, f"plant {strings['plant_id']} docs")
    cv.refuse_first((
        (not _STEM.match(strings["plant_id"]), cv.FINDING_PLANT_FIELD_INVALID,
         f"plant_id {cv.shown(strings['plant_id'])} is not a slug"),
        (not _STEM.match(strings["fail_id"]), cv.FINDING_PLANT_FIELD_INVALID,
         f"fail_id {cv.shown(strings['fail_id'])} is not a slug"),
        (not _IDENT.match(strings["module"]), cv.FINDING_PLANT_FIELD_INVALID,
         f"module {cv.shown(strings['module'])} is not an identifier"),
        (not _IDENT.match(strings["drop_module"]), cv.FINDING_PLANT_FIELD_INVALID,
         f"drop_module {cv.shown(strings['drop_module'])} is not an identifier"),
    ))
    return cat.Plant(
        plant_id=strings["plant_id"],
        fail_id=strings["fail_id"],
        provider=strings["provider"],
        identity_field=strings["identity_field"],
        event_field=strings["event_field"],
        naive_field=strings["naive_field"],
        docs=(docs[0], docs[1]),
        ticket=strings["ticket"],
        module=strings["module"],
        drop_module=strings["drop_module"],
        test_ok=strings["test_ok"],
        test_fail=strings["test_fail"],
        short=strings["short"],
        dshort=strings["dshort"],
    )


def _check_uniques(plants: tuple[cat.Plant, ...]) -> None:
    axes = {
        "plant_id": [item.plant_id for item in plants],
        "fail_id": [item.fail_id for item in plants],
        "module": [item.module for item in plants],
        "drop_module": [item.drop_module for item in plants],
        "ticket": [item.ticket for item in plants],
        "bind": [(item.provider, item.identity_field, item.event_field) for item in plants],
    }
    for name, values in axes.items():
        cv.refuse_when(
            len(values) != len(set(values)),
            cv.FINDING_PLANT_ID_DUPLICATE,
            f"catalog duplicates {name}",
        )


def load_catalog(directory: Path | str) -> cat.Catalog:
    """Load ``CATALOG.json`` and ``plants.jsonl``; refuse a drifted plants digest."""
    root = Path(directory)
    cv.refuse_when(not root.is_dir(), cv.FINDING_CATALOG_FILE_MISSING, f"catalog dir {root}")
    header_raw = _read(root / cat.CATALOG_FILENAME, cv.FINDING_CATALOG_FILE_MISSING)
    plants_raw = _read(root / cat.PLANTS_FILENAME, cv.FINDING_CATALOG_FILE_MISSING)
    _refuse_banned_text(plants_raw.decode("utf-8"), "plants.jsonl")
    header = load_strict_json(header_raw.decode("utf-8"))
    cv.refuse_when(
        not isinstance(header, dict),
        cv.FINDING_INPUT_NOT_AN_OBJECT,
        "CATALOG.json must be an object",
    )
    for key in ("catalog_id", "format", "family", "plant_count", "plants_filename", "plants_sha256"):
        cv.refuse_when(key not in header, cv.FINDING_CATALOG_FIELD_MISSING, f"CATALOG.json missing {key}")
    cv.refuse_first((
        (header["catalog_id"] != cv.CATALOG_ID, cv.FINDING_CATALOG_FIELD_INVALID,
         f"catalog_id {cv.shown(header['catalog_id'])} is not {cv.CATALOG_ID}"),
        (header["format"] != cv.CATALOG_FORMAT, cv.FINDING_CATALOG_FIELD_INVALID,
         f"format {cv.shown(header['format'])} is not {cv.CATALOG_FORMAT}"),
        (header["family"] != cv.FAMILY, cv.FINDING_CATALOG_FIELD_INVALID,
         f"family {cv.shown(header['family'])} is not {cv.FAMILY}"),
        (header["plants_filename"] != cat.PLANTS_FILENAME, cv.FINDING_CATALOG_FIELD_INVALID,
         f"plants_filename {cv.shown(header['plants_filename'])} is not {cat.PLANTS_FILENAME}"),
        (sha256_bytes(plants_raw) != header["plants_sha256"], cv.FINDING_PLANTS_SHA_MISMATCH,
         "plants.jsonl digest differs from CATALOG.json plants_sha256"),
    ))
    plants = []
    for index, line in enumerate(plants_raw.decode("utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        plants.append(_plant_from_row(load_strict_json(line), index))
    cv.refuse_when(
        len(plants) != header["plant_count"],
        cv.FINDING_CATALOG_FIELD_INVALID,
        f"plant_count {cv.shown(header['plant_count'])} != {len(plants)} rows",
    )
    loaded = tuple(plants)
    _check_uniques(loaded)
    return cat.Catalog(
        catalog_id=header["catalog_id"],
        format=header["format"],
        family=header["family"],
        plant_count=len(loaded),
        plants_sha256=header["plants_sha256"],
        plants=loaded,
        header=header,
    )


bind_import_twin(__name__)
