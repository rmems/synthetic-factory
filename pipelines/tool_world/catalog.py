#!/usr/bin/env python3
"""The pinned catalog of world packs: ``catalogs/tool-world-v1/CATALOG.json``.

The catalog names every pack and pins its digest; loading recomputes each
pack digest and refuses a drifted member. ``catalog_sha256`` is the digest
of the sorted ``[pack_id, pack_sha256]`` pairs, so it changes when any pack
byte changes and never when only the catalog prose does.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import pack as pk
from . import vocabulary as cv
from ._contract import bind_import_twin, dumps_exact_json, load_strict_json, sha256_canonical

__all__ = ["DEFAULT_CATALOG", "Catalog", "catalog_digest", "load_catalog", "write_pins"]

CATALOG_FILENAME = "CATALOG.json"
_REPO = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = _REPO / "catalogs" / "tool-world-v1"


@dataclass(frozen=True)
class Catalog:
    catalog_id: str
    directory: Path
    packs: tuple[pk.Pack, ...]
    catalog_sha256: str

    def pack(self, pack_id: str) -> pk.Pack:
        for member in self.packs:
            if member.pack_id == pack_id:
                return member
        raise cv.ToolWorldRefusal(
            cv.FINDING_PACK_FILE_MISSING, f"pack {pack_id!r} is not in catalog {self.catalog_id}"
        )

    def tasks(self, factory: str | None = None) -> Iterator[tuple[pk.Pack, pk.Task]]:
        """Every ``(pack, task)`` pair, in pack then task order, optionally for one factory."""
        for member in self.packs:
            for task in member.tasks:
                if factory is None or task.factory == factory:
                    yield member, task


def catalog_digest(packs: tuple[pk.Pack, ...]) -> str:
    return sha256_canonical(sorted([member.pack_id, member.pack_sha256] for member in packs))


def _header(directory: Path) -> Mapping[str, Any]:
    path = directory / CATALOG_FILENAME
    cv.refuse_when(
        not path.is_file(),
        cv.FINDING_CATALOG_FILE_MISSING,
        f"missing {CATALOG_FILENAME} in {directory.name}",
    )
    try:
        header = load_strict_json(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise cv.ToolWorldRefusal(
            cv.FINDING_CATALOG_FIELD_INVALID, f"{CATALOG_FILENAME} is not strict JSON ({exc})"
        ) from exc
    cv.refuse_when(
        not isinstance(header, Mapping),
        cv.FINDING_CATALOG_FIELD_INVALID,
        f"{CATALOG_FILENAME} must be an object",
    )
    cv.refuse_first(
        (
            (
                header.get("format") != cv.CATALOG_FORMAT,
                cv.FINDING_CATALOG_FIELD_INVALID,
                f"format must be {cv.CATALOG_FORMAT}",
            ),
            (
                header.get("family") != cv.FAMILY,
                cv.FINDING_CATALOG_FIELD_INVALID,
                f"family must be {cv.FAMILY}",
            ),
            (
                not isinstance(header.get("catalog_id"), str) or not header["catalog_id"],
                cv.FINDING_CATALOG_FIELD_INVALID,
                "catalog_id must be a nonempty string",
            ),
            (
                not isinstance(header.get("packs"), list) or not header["packs"],
                cv.FINDING_CATALOG_FIELD_INVALID,
                "packs must be a nonempty list",
            ),
        )
    )
    return header


def _row_pack(directory: Path, row: Any, where: str) -> pk.Pack:
    """The pack a catalog row names, loaded from its current bytes."""
    cv.refuse_when(
        not isinstance(row, Mapping) or not isinstance(row.get("pack_id"), str),
        cv.FINDING_CATALOG_FIELD_INVALID,
        f"{where}: must carry a pack_id string",
    )
    return pk.load_pack(directory / row["pack_id"])


def load_catalog(directory: Path | None = None) -> Catalog:
    """Load every pinned pack; a pack whose bytes drifted from its pin is refused."""
    directory = Path(directory) if directory is not None else DEFAULT_CATALOG
    header = _header(directory)
    packs = []
    for index, row in enumerate(header["packs"]):
        where = f"packs[{index}]"
        member = _row_pack(directory, row, where)
        cv.refuse_when(
            not isinstance(row.get("pack_sha256"), str),
            cv.FINDING_CATALOG_FIELD_INVALID,
            f"{where}: must carry a pack_sha256 string",
        )
        cv.refuse_when(
            member.pack_sha256 != row["pack_sha256"],
            cv.FINDING_PACK_SHA_MISMATCH,
            f"{where}: pack {member.pack_id} digest {member.pack_sha256} "
            f"is not the pinned {row['pack_sha256']}",
        )
        packs.append(member)
    ids = [member.pack_id for member in packs]
    cv.refuse_when(
        len(set(ids)) != len(ids), cv.FINDING_CATALOG_FIELD_INVALID, "duplicate pack ids"
    )
    return Catalog(
        catalog_id=header["catalog_id"],
        directory=directory,
        packs=tuple(packs),
        catalog_sha256=catalog_digest(tuple(packs)),
    )


def write_pins(directory: Path | None = None) -> Catalog:
    """Re-pin every pack the header names from its current bytes, then load the catalog.

    The one tool-world writer that refreshes a file in place: ``CATALOG.json`` is
    the index of reviewed pack digests, refreshed like ``NEXT_ROUND.json`` after an
    intentional pack edit. Rows keep their order and prose; only ``surfaces`` and
    ``pack_sha256`` are rewritten, and the result must load like any other catalog.
    """
    directory = Path(directory) if directory is not None else DEFAULT_CATALOG
    header = dict(_header(directory))
    rows = []
    for index, row in enumerate(header["packs"]):
        member = _row_pack(directory, row, f"packs[{index}]")
        rows.append({**row, "surfaces": list(member.surfaces), "pack_sha256": member.pack_sha256})
    header["packs"] = rows
    path = directory / CATALOG_FILENAME
    path.write_text(dumps_exact_json(header, indent=2) + "\n", encoding="utf-8", newline="")
    return load_catalog(directory)


bind_import_twin(__name__)
