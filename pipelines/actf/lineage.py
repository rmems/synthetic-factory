#!/usr/bin/env python3
"""Read recover-grok ACTF lineages. Paths only; source bytes stay unread here."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import vocabulary as cv
from ._contract import bind_import_twin, load_strict_json

__all__ = [
    "FragmentRef",
    "Lineage",
    "VersionRef",
    "by_original_path",
    "read_lineage",
    "read_recovery_tree",
]


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


@dataclass(frozen=True)
class VersionRef:
    """One recovered version file. The reader does not open it."""

    path_key: str
    version_label: str
    source_path: Path
    basename: str

    @property
    def version_id(self) -> str:
        return f"{self.path_key}:{self.version_label}"


@dataclass(frozen=True)
class FragmentRef:
    """One old/new ``.pyfrag`` pair. Missing sides stay ``None``."""

    path_key: str
    call_id: str
    old_path: Path | None
    new_path: Path | None


@dataclass(frozen=True)
class Lineage:
    """One ``actf-*`` recover-grok path lineage."""

    path_key: str
    original_path: str
    original_basename: str
    classification: str
    version_count: int
    versions: tuple[VersionRef, ...]
    fragments: tuple[FragmentRef, ...]
    lineage_dir: Path

    @property
    def is_recoverable(self) -> bool:
        return self.classification != cv.CLASSIFICATION_UNRECOVERABLE


def by_original_path(recovery_root: Path) -> Path:
    """``recovered_sources/by-original-path``, or ``recovery_root`` when it is that dir."""

    nested = recovery_root / "recovered_sources" / "by-original-path"
    if nested.is_dir():
        return nested
    if recovery_root.name == "by-original-path" and recovery_root.is_dir():
        return recovery_root
    return nested


def _required_string(payload: dict[str, Any], field: str, lineage_dir: Path) -> str:
    value = payload.get(field)
    cv.refuse_when(
        not isinstance(value, str) or not value,
        cv.FINDING_PATH_JSON_INVALID,
        f"{lineage_dir.name} path.json {field} must be a non-empty string, got {cv.shown(value)}",
    )
    return value


def _list_versions(lineage_dir: Path, path_key: str, basename: str) -> tuple[VersionRef, ...]:
    versions_root = lineage_dir / cv.VERSIONS_DIR
    if not versions_root.is_dir():
        return ()
    found: list[VersionRef] = []
    for child in sorted(versions_root.iterdir(), key=lambda item: item.name):
        if not child.is_dir() or not child.name.startswith("v"):
            continue
        source = child / basename
        if source.is_file():
            found.append(
                VersionRef(
                    path_key=path_key,
                    version_label=child.name,
                    source_path=source,
                    basename=basename,
                )
            )
    return tuple(found)


def _list_fragments(lineage_dir: Path, path_key: str, basename: str) -> tuple[FragmentRef, ...]:
    fragments_root = lineage_dir / cv.FRAGMENTS_DIR
    if not fragments_root.is_dir():
        return ()
    found: list[FragmentRef] = []
    for child in sorted(fragments_root.iterdir(), key=lambda item: item.name):
        if not child.is_dir():
            continue
        old_path = child / f"{basename}.old.pyfrag"
        new_path = child / f"{basename}.new.pyfrag"
        found.append(
            FragmentRef(
                path_key=path_key,
                call_id=child.name,
                old_path=old_path if old_path.is_file() else None,
                new_path=new_path if new_path.is_file() else None,
            )
        )
    return tuple(found)


def read_lineage(lineage_dir: Path) -> Lineage:
    """Load one ACTF lineage from ``path.json`` plus version and fragment paths."""

    cv.refuse_when(
        not lineage_dir.is_dir(),
        cv.FINDING_LINEAGE_DIR_INVALID,
        f"lineage path is not a directory: {cv.shown(str(lineage_dir))}",
    )
    path_json = lineage_dir / cv.PATH_JSON_NAME
    cv.refuse_when(
        not path_json.is_file(),
        cv.FINDING_PATH_JSON_INVALID,
        f"{lineage_dir.name} is missing {cv.PATH_JSON_NAME}",
    )
    try:
        payload = load_strict_json(path_json.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        cv.refuse(
            cv.FINDING_PATH_JSON_INVALID,
            f"{lineage_dir.name} path.json is not strict JSON: {exc}",
        )
    cv.refuse_when(
        not isinstance(payload, dict),
        cv.FINDING_PATH_JSON_INVALID,
        f"{lineage_dir.name} path.json must be an object, got {cv.shown(type(payload).__name__)}",
    )
    path_key = _required_string(payload, "path_key", lineage_dir)
    cv.refuse_when(
        path_key != lineage_dir.name,
        cv.FINDING_PATH_KEY_MISMATCH,
        f"path_key {cv.shown(path_key)} does not match directory {cv.shown(lineage_dir.name)}",
    )
    classification = _required_string(payload, "classification", lineage_dir)
    cv.refuse_when(
        classification not in cv.CLASSIFICATION_SET,
        cv.FINDING_UNKNOWN_CLASSIFICATION,
        f"{path_key} classification {cv.shown(classification)} is not declared",
    )
    original_path = _required_string(payload, "original_path", lineage_dir)
    original_basename = _required_string(payload, "original_basename", lineage_dir)
    version_count = payload.get("version_count")
    cv.refuse_when(
        not _is_int(version_count) or version_count < 0,
        cv.FINDING_PATH_JSON_INVALID,
        f"{path_key} version_count must be a non-negative int, got {cv.shown(version_count)}",
    )
    versions = _list_versions(lineage_dir, path_key, original_basename)
    cv.refuse_when(
        len(versions) != version_count,
        cv.FINDING_VERSION_COUNT_MISMATCH,
        f"{path_key} version_count={version_count} but found {len(versions)} version files",
    )
    return Lineage(
        path_key=path_key,
        original_path=original_path,
        original_basename=original_basename,
        classification=classification,
        version_count=version_count,
        versions=versions,
        fragments=_list_fragments(lineage_dir, path_key, original_basename),
        lineage_dir=lineage_dir,
    )


def read_recovery_tree(recovery_root: Path) -> tuple[Lineage, ...]:
    """Enumerate ``actf-*`` lineages under a recover-grok session root."""

    root = Path(recovery_root)
    listed = by_original_path(root)
    cv.refuse_when(
        not listed.is_dir(),
        cv.FINDING_RECOVERY_ROOT_MISSING,
        f"recovery tree has no {cv.BY_ORIGINAL_PATH}: {cv.shown(str(root))}",
    )
    lineages: list[Lineage] = []
    for child in sorted(listed.iterdir(), key=lambda item: item.name):
        if child.is_dir() and child.name.startswith(cv.LINEAGE_PREFIX):
            lineages.append(read_lineage(child))
    return tuple(lineages)


bind_import_twin(__name__)
