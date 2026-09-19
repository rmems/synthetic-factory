"""Descriptor-pinned filesystem transaction primitives for oracle generation."""

import errno
import fcntl
import os
from pathlib import Path
import stat
import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("oracle_generate_fs")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_generate_fs"
    )


class GenerationFilesystem:

    def __init__(self, api):
        self.api = api

    def _raw_containment_error(self, resolved, out_dir):
        """The refusal for a fully resolved path inside ``outputs/raw/``, or None."""
        raw_root = Path(os.path.realpath(self.api.RAW_TREE))
        if resolved == raw_root or raw_root in resolved.parents:
            return f'{out_dir} resolves into the immutable raw tree {self.api.RAW_TREE}; outputs/raw/ is never a generation destination'
        return None

    def _raw_destination_error(self, out_dir):
        """Why ``out_dir`` may not be used, or None. Runs before anything is written.

    ``reserve_run`` creates a sibling lock before the staging tree exists, so a
    destination beneath the repository's immutable ``outputs/raw/`` tree must be
    refused before the reservation -- including a path that only resolves there
    through symlinks.  An unresolvable path is refused rather than trusted.
    """
        try:
            resolved = Path(os.path.realpath(out_dir))
            return self.api._raw_containment_error(resolved, out_dir)
        except (OSError, ValueError) as exc:
            return f'could not resolve {out_dir} against the immutable raw tree: {type(exc).__name__}'

    def _locked_lock_descriptor(self, lock_path, dir_fd=None):
        """Open, authenticate, and exclusively lock one reservation file.

    The descriptor is closed on any failure after the open; the open itself
    propagates without a descriptor to clean up.  With ``dir_fd`` the lock
    name is resolved relative to an already-authenticated parent descriptor,
    so a racing ancestor swap cannot redirect the lock.
    """
        descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR | getattr(os, 'O_CLOEXEC', 0) | getattr(os, 'O_NOFOLLOW', 0), 384, dir_fd=dir_fd)
        try:
            lock_stat = os.fstat(descriptor)
            if not stat.S_ISREG(lock_stat.st_mode) or lock_stat.st_nlink != 1:
                raise OSError(errno.EINVAL, 'reservation lock is not a regular file')
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(descriptor)
            raise
        return descriptor

    def _claim_reservation_lock(self, lock_name, parent, parent_fd):
        """Take the exclusive reservation lock, or report the owning generation."""
        try:
            return self.api._locked_lock_descriptor(lock_name, dir_fd=parent_fd)
        except (BlockingIOError, FileExistsError) as exc:
            raise FileExistsError(f'another generation owns reservation {parent / lock_name}') from exc

    def _assert_destination_absent(self, out_dir, parent_fd):
        """Refuse an existing destination while the reservation lock is held."""
        exists = True
        if out_dir.name:
            try:
                os.lstat(out_dir.name, dir_fd=parent_fd)
            except FileNotFoundError:
                exists = False
        if exists:
            raise FileExistsError(f'refusing to overwrite existing run {out_dir}')

    def _claimed_reservation(self, out_dir, parent, parent_fd):
        """The held reservation lock after proving the destination is absent."""
        stem = out_dir.name or 'oracle-run'
        lock_name = f'.{stem}.oracle-generate.lock'
        descriptor = self.api._claim_reservation_lock(lock_name, parent, parent_fd)
        try:
            self.api._assert_destination_absent(out_dir, parent_fd)
        except BaseException:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)
            raise
        return descriptor

    def reserve_run(self, out_dir):
        """Hold a kernel lock for this output name for the full transaction.

    Returns ``(lock_descriptor, parent_fd)``; the caller owns both.  The
    reservation lock, the staging tree, and the publication rename all go
    through ``parent_fd``, so an ancestor swapped for a symlink after the
    static destination check can no longer redirect any of those writes.
    """
        parent = out_dir.parent
        parent_fd = self.api._create_pinned_parent(parent, out_dir)
        try:
            descriptor = self.api._claimed_reservation(out_dir, parent, parent_fd)
        except BaseException:
            os.close(parent_fd)
            raise
        return (descriptor, parent_fd)

    def _directory_identity(self, path):
        state = os.lstat(path)
        if not stat.S_ISDIR(state.st_mode):
            raise OSError(errno.ENOTDIR, 'publication source is not a directory', os.fspath(path))
        return (state.st_dev, state.st_ino)

    def _verify_requested_publication(self, out_dir, parent_fd, published_identity=None):
        """Bind descriptor-relative publication back to the caller's pathname."""
        requested = os.stat(out_dir.parent)
        pinned = os.fstat(parent_fd)
        if (requested.st_dev, requested.st_ino) != (pinned.st_dev, pinned.st_ino):
            raise OSError(errno.ESTALE, 'requested parent no longer matches the pinned directory')
        if published_identity is not None and self.api._directory_identity(out_dir) != published_identity:
            raise OSError(errno.ESTALE, 'requested output no longer matches the published directory')

if __package__:
    _expose_package_sibling(__name__)
