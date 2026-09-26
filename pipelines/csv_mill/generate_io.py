"""Stage CSV replay files and publish their directory without overwriting."""

from __future__ import annotations

import fcntl
import os
import stat
import tempfile
from pathlib import Path

from ._contract import (
    CsvRefusal,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_INVALID,
    FINDING_DESTINATION_UNDER_RAW,
    bind_import_twin,
    safe_under_raw,
)
from .generate_parent import pinned_parent, release_descriptor, verify_parent

if __name__.startswith("pipelines."):
    from ..compose_destination_rename import rename_noreplace
else:
    from compose_destination_rename import rename_noreplace

__all__ = ["write_run_files"]

_STAGE_CHANGED = "private staging directory changed"


def _identity(metadata):
    return metadata.st_dev, metadata.st_ino


def _same_entry(path, descriptor):
    try:
        return _identity(path.lstat()) == _identity(os.fstat(descriptor))
    except OSError:
        return False


def _lock_entry(descriptor):
    fcntl.flock(descriptor, fcntl.LOCK_EX)


def _unlock_entry(descriptor):
    try:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
    except OSError:
        # Unlock is best-effort; the descriptor is still released by the caller.
        pass


def _if_still(predicate, action):
    """Run action only when the identity predicate holds twice in a row."""

    try:
        if predicate() and predicate():
            action()
    except OSError:
        # Replacements observed before the last check stay; never broaden cleanup.
        pass


def _remove_empty_entry(path, identity):
    def owned():
        return _identity(path.lstat()) == identity

    _if_still(owned, lambda: os.rmdir(path))


def _open_stage(path, identity):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        if _identity(os.fstat(descriptor)) != identity:
            raise CsvRefusal(FINDING_DESTINATION_INVALID, _STAGE_CHANGED)
    except BaseException:
        release_descriptor(descriptor)
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

    def same_inode(self, directory, name):
        try:
            current = os.stat(name, dir_fd=directory, follow_symlinks=False)
            return _identity(current) == _identity(os.fstat(self.descriptor))
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
        def still_owned():
            return owned.matches(self.descriptor, name)

        _if_still(still_owned, lambda: os.unlink(name, dir_fd=self.descriptor))

    def cleanup(self):
        _lock_entry(self.descriptor)
        try:
            for name, owned in self.files.items():
                self._unlink_owned(name, owned)
            _remove_empty_entry(self.path, _identity(os.fstat(self.descriptor)))
        finally:
            _unlock_entry(self.descriptor)

    def close(self):
        for owned in self.files.values():
            release_descriptor(owned.descriptor)
        release_descriptor(self.descriptor)

    def publish(self, parent, destination, descriptor):
        published = parent.resolve(strict=True) / destination.name
        _authenticate_commit(parent, self.path, destination, self)
        rename_noreplace(descriptor, self.path.name, destination.name)
        return _confirm_commit(parent, published, self)


def _discard_owned_inode(directory, name, owned):
    """Drop our inode's directory entry even when its bytes were mutated."""

    try:
        if owned.same_inode(directory, name):
            os.unlink(name, dir_fd=directory)
    except OSError:
        pass


def _live_path(descriptor):
    try:
        return Path(os.readlink(f"/proc/self/fd/{descriptor}"))
    except OSError:
        return None


def _rmdir_owned(published, stage):
    candidates = [published]
    live = _live_path(stage.descriptor)
    if live is not None:
        candidates.append(live)
    for candidate in candidates:
        try:
            if _same_entry(candidate, stage.descriptor):
                os.rmdir(candidate)
                return
        except OSError:
            continue


def _rollback_owned_publication(published, stage):
    for name, owned in stage.files.items():
        _discard_owned_inode(stage.descriptor, name, owned)
    _rmdir_owned(published, stage)


def _refuse_if_raw(path):
    if safe_under_raw(path):
        raise CsvRefusal(FINDING_DESTINATION_UNDER_RAW, "publication landed under the raw tree")


def _authenticate_commit(parent, staged, destination, stage):
    stage.verify()
    verify_parent(destination, parent)
    if not _same_entry(staged, stage.descriptor):
        raise CsvRefusal(FINDING_DESTINATION_INVALID, _STAGE_CHANGED)


def _parent_matches(live, parent):
    try:
        return _identity(live.parent.lstat()) == _identity(parent.stat())
    except OSError:
        return False


def _confirm_commit(parent, published, stage):
    live = _live_path(stage.descriptor) or published
    try:
        _refuse_if_raw(parent)
        _refuse_if_raw(live)
        stage.verify()
        if not _parent_matches(live, parent):
            raise CsvRefusal(FINDING_DESTINATION_INVALID, "output parent changed during publication")
    except BaseException:
        _rollback_owned_publication(live, stage)
        raise
    return live


def _publish(parent: Path, staged: Path, destination: Path, stage: _OwnedStage) -> Path:
    descriptor = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        _lock_entry(stage.descriptor)
        try:
            if not _same_entry(staged, stage.descriptor):
                raise CsvRefusal(FINDING_DESTINATION_INVALID, _STAGE_CHANGED)
            return stage.publish(parent, destination, descriptor)
        finally:
            _unlock_entry(stage.descriptor)
    except FileExistsError as exc:
        raise CsvRefusal(
            FINDING_DESTINATION_EXISTS, f"{destination} already exists"
        ) from exc
    finally:
        release_descriptor(descriptor)


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
