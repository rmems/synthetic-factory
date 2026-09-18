"""Stage CSV replay files and publish their directory without overwriting."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from ._contract import (
    CsvRefusal, FINDING_DESTINATION_EXISTS, FINDING_DESTINATION_INVALID, bind_import_twin,
)
from .generate_parent import pinned_parent, verify_parent

if __name__.startswith("pipelines."):
    from ..compose_destination_rename import rename_noreplace
else:
    from compose_destination_rename import rename_noreplace

__all__ = ["write_run_files"]


def _publish(parent: Path, staged: Path, destination: Path) -> None:
    descriptor = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        # This detects observable relocation before commit. A directory FD
        # pins an inode, not its namespace: another actor can still move that
        # inode between this check and rename, or after publication succeeds.
        verify_parent(destination, parent)
        rename_noreplace(descriptor, staged.name, destination.name)
    except FileExistsError as exc:
        raise CsvRefusal(
            FINDING_DESTINATION_EXISTS, f"{destination} already exists"
        ) from exc
    finally:
        os.close(descriptor)


def _stage_and_publish(parent: Path, destination: Path, files: dict[str, str]) -> Path:
    published = parent.resolve(strict=True) / destination.name
    # After rename, this old stage name can belong to another writer. Cleanup is
    # restricted to the precommit failure path, never the published destination.
    staging = tempfile.TemporaryDirectory(prefix=".csv-stage-", dir=parent, delete=False)
    try:
        staged = Path(staging.name)
        for name, payload in files.items():
            (staged / name).write_text(payload, encoding="utf-8")
        _publish(parent, staged, destination)
    except BaseException:
        staging.cleanup()
        raise
    return published


def write_run_files(destination: Path, files: dict[str, str]) -> Path:
    """Expose a complete run and return its anchored publication location."""
    try:
        with pinned_parent(destination) as parent:
            return _stage_and_publish(parent, destination, files)
    except OSError as exc:
        raise CsvRefusal(FINDING_DESTINATION_INVALID, str(exc)) from exc


bind_import_twin(__name__)
