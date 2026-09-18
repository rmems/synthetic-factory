"""Stage CSV replay files and publish their directory without overwriting."""

from __future__ import annotations

import os
import stat
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


def _remove_empty_entry(path, identity):
    try:
        if _identity(path.lstat()) == identity:
            os.rmdir(path)
    except OSError:
        # Replacements observed before the check and nonempty directories stay.
        pass


def _open_stage(path, identity):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        if _identity(os.fstat(descriptor)) != identity:
            raise CsvRefusal(FINDING_DESTINATION_INVALID, "private staging directory changed")
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


class _StageFile:
    """Authenticate the bytes written through the original readable descriptor."""

    def __init__(self, directory, name):
        self.descriptor = os.open(name, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                  0o666, dir_fd=directory)
        self.expected = b""

    def write(self, payload):
        pending = payload.encode("utf-8")
        while pending:
            written = os.write(self.descriptor, pending)
            if written == 0:
                raise OSError("staged file write made no progress")
            self.expected += pending[:written]
            pending = pending[written:]

    def matches(self, directory, name):
        try:
            current = os.stat(name, dir_fd=directory, follow_symlinks=False)
            owned = os.fstat(self.descriptor)
            return (
                stat.S_ISREG(current.st_mode)
                and _identity(current) == _identity(owned)
                and owned.st_size == len(self.expected)
                and os.pread(self.descriptor, len(self.expected) + 1, 0) == self.expected
            )
        except OSError:
            return False


class _OwnedStage:
    """Hold the created directory and files until publication or owned cleanup."""

    def __init__(self, parent):
        self.path = Path(tempfile.mkdtemp(prefix=".csv-stage-", dir=parent))
        identity = _identity(self.path.lstat())
        try:
            self.descriptor = _open_stage(self.path, identity)
        except BaseException:
            _remove_empty_entry(self.path, identity)
            raise
        self.files = {}

    def write(self, name, payload):
        owned = _StageFile(self.descriptor, name)
        self.files[name] = owned
        owned.write(payload)

    def verify(self):
        # Open a fresh directory stream; the long-lived FD can cache old entries.
        if set(os.listdir(f"/proc/self/fd/{self.descriptor}")) != set(self.files):
            raise CsvRefusal(FINDING_DESTINATION_INVALID, "private staging entries changed")
        for name, owned in self.files.items():
            if not owned.matches(self.descriptor, name):
                raise CsvRefusal(FINDING_DESTINATION_INVALID, f"staged file {name} changed")

    def _unlink_owned(self, name, owned):
        # A same-UID actor can still replace the entry between this check and unlink.
        try:
            if owned.matches(self.descriptor, name):
                os.unlink(name, dir_fd=self.descriptor)
        except OSError:
            # Never broaden cleanup after an ownership or filesystem failure.
            pass

    def cleanup(self):
        for name, owned in self.files.items():
            self._unlink_owned(name, owned)
        _remove_empty_entry(self.path, _identity(os.fstat(self.descriptor)))

    def close(self):
        for owned in self.files.values():
            os.close(owned.descriptor)
        os.close(self.descriptor)


def _publish(parent: Path, staged: Path, destination: Path, stage: _OwnedStage) -> Path:
    descriptor = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        stage.verify()
        # This detects observable relocation before commit. A directory FD
        # pins an inode, not its namespace: another actor can still move that
        # inode between this check and rename, or after publication succeeds.
        verify_parent(destination, parent)
        published = parent.resolve(strict=True) / destination.name
        if not _same_entry(staged, stage.descriptor):
            raise CsvRefusal(FINDING_DESTINATION_INVALID, "private staging directory changed")
        rename_noreplace(descriptor, staged.name, destination.name)
        return published
    except FileExistsError as exc:
        raise CsvRefusal(
            FINDING_DESTINATION_EXISTS, f"{destination} already exists"
        ) from exc
    finally:
        os.close(descriptor)


def _stage_and_publish(parent: Path, destination: Path, files: dict[str, str]) -> Path:
    stage = _OwnedStage(parent)
    try:
        for name, payload in files.items():
            stage.write(name, payload)
        return _publish(parent, stage.path, destination, stage)
    except BaseException:
        stage.cleanup()
        raise
    finally:
        stage.close()


def write_run_files(destination: Path, files: dict[str, str]) -> Path:
    """Expose a complete run and return its anchored publication location."""
    try:
        with pinned_parent(destination) as parent:
            return _stage_and_publish(parent, destination, files)
    except OSError as exc:
        raise CsvRefusal(FINDING_DESTINATION_INVALID, str(exc)) from exc


bind_import_twin(__name__)
