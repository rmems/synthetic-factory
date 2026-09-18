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


def _identity(metadata):
    return metadata.st_dev, metadata.st_ino


def _same_entry(path, descriptor):
    try:
        return _identity(path.lstat()) == _identity(os.fstat(descriptor))
    except OSError:
        return False


class _OwnedStage:
    """Hold the created directory and files until publication or owned cleanup."""

    def __init__(self, parent):
        self.path = Path(tempfile.mkdtemp(prefix=".csv-stage-", dir=parent))
        self.descriptor = os.open(self.path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        self.files = {}

    def write(self, name, payload):
        descriptor = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o666, dir_fd=self.descriptor)
        self.files[name] = descriptor
        with os.fdopen(descriptor, "w", encoding="utf-8", closefd=False) as handle:
            handle.write(payload)

    def _unlink_owned(self, name, descriptor):
        try:
            current = os.stat(name, dir_fd=self.descriptor, follow_symlinks=False)
            if _identity(current) == _identity(os.fstat(descriptor)):
                os.unlink(name, dir_fd=self.descriptor)
        except OSError:
            # Never broaden cleanup after an ownership or filesystem failure.
            pass

    def cleanup(self):
        for name, descriptor in self.files.items():
            self._unlink_owned(name, descriptor)
        if _same_entry(self.path, self.descriptor):
            try:
                os.rmdir(self.path)
            except OSError:
                # Unknown content or a changed entry stays intact.
                pass

    def close(self):
        for descriptor in self.files.values():
            os.close(descriptor)
        os.close(self.descriptor)


def _publish(parent: Path, staged: Path, destination: Path, stage_descriptor: int) -> None:
    descriptor = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        # This detects observable relocation before commit. A directory FD
        # pins an inode, not its namespace: another actor can still move that
        # inode between this check and rename, or after publication succeeds.
        verify_parent(destination, parent)
        if not _same_entry(staged, stage_descriptor):
            raise CsvRefusal(FINDING_DESTINATION_INVALID, "private staging directory changed")
        rename_noreplace(descriptor, staged.name, destination.name)
    except FileExistsError as exc:
        raise CsvRefusal(
            FINDING_DESTINATION_EXISTS, f"{destination} already exists"
        ) from exc
    finally:
        os.close(descriptor)


def _stage_and_publish(parent: Path, destination: Path, files: dict[str, str]) -> Path:
    published = parent.resolve(strict=True) / destination.name
    stage = _OwnedStage(parent)
    try:
        for name, payload in files.items():
            stage.write(name, payload)
        _publish(parent, stage.path, destination, stage.descriptor)
    except BaseException:
        stage.cleanup()
        raise
    finally:
        stage.close()
    return published


def write_run_files(destination: Path, files: dict[str, str]) -> Path:
    """Expose a complete run and return its anchored publication location."""
    try:
        with pinned_parent(destination) as parent:
            return _stage_and_publish(parent, destination, files)
    except OSError as exc:
        raise CsvRefusal(FINDING_DESTINATION_INVALID, str(exc)) from exc


bind_import_twin(__name__)
