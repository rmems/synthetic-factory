"""Descriptor-pinned filesystem transaction primitives for oracle generation."""

import ctypes
import errno
import fcntl
import os
from pathlib import Path
import secrets
import stat
import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("oracle_generate_fs")
    from .compose_contract import ComposeError
    from .compose_destination_rename import quarantine_owned_entry
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_generate_fs"
    )
    from compose_contract import ComposeError
    from compose_destination_rename import quarantine_owned_entry


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

    def _pinned_parent_descriptor(self, parent, out_dir):
        """Open and authenticate the run's parent directory for the transaction.

    ``_raw_destination_error`` checks the path before anything exists, but a
    non-cooperating process can swap a checked ancestor for a symlink into
    ``outputs/raw/`` after that check returns.  Every later write of the
    transaction goes through this descriptor, so this authentication is the
    one that counts: the kernel reports where the descriptor really landed,
    and a parent inside the raw tree is refused no matter what the path
    components claimed.  Platforms without ``/proc`` descriptor resolution
    fail closed, exactly like the ``renameat2`` publication point.
    """
        parent_fd = os.open(parent, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0) | getattr(os, 'O_CLOEXEC', 0))
        try:
            self.api._authenticate_parent_descriptor(parent_fd, out_dir)
        except BaseException:
            os.close(parent_fd)
            raise
        return parent_fd

    def _authenticate_parent_descriptor(self, parent_fd, out_dir):
        try:
            true_parent = Path(os.readlink(f'/proc/self/fd/{parent_fd}'))
        except OSError as exc:
            raise OSError(errno.ENOSYS, 'cannot authenticate the run parent without /proc descriptor resolution') from exc
        error = self.api._raw_containment_error(true_parent, out_dir)
        if error is not None:
            raise OSError(errno.EACCES, error)

    def _open_created_parent(self, parent_fd, component, out_dir):
        candidate = Path(f'/proc/self/fd/{parent_fd}') / component
        error = self.api._raw_destination_error(candidate)
        if error is not None:
            raise OSError(errno.EACCES, error)
        try:
            os.mkdir(component, dir_fd=parent_fd)
        except FileExistsError:
            pass
        child_fd = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent_fd)
        try:
            self.api._authenticate_parent_descriptor(child_fd, out_dir)
        except BaseException:
            os.close(child_fd)
            raise
        return child_fd

    def _create_pinned_parent(self, parent, out_dir):
        """Authenticate the existing ancestor before creating missing descendants."""
        missing = []
        existing = parent
        while not existing.exists():
            missing.append(existing.name)
            if existing == existing.parent:
                raise OSError(errno.ENOENT, 'no accessible output ancestor')
            existing = existing.parent
        parent_fd = self.api._pinned_parent_descriptor(existing, out_dir)
        try:
            for component in reversed(missing):
                child_fd = self.api._open_created_parent(parent_fd, component, out_dir)
                os.close(parent_fd)
                parent_fd = child_fd
        except BaseException:
            os.close(parent_fd)
            raise
        return parent_fd

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

    def reserve_run(self, out_dir):
        """Hold a kernel lock for this output name for the full transaction.

    Returns ``(lock_descriptor, parent_fd)``; the caller owns both.  The
    reservation lock, the staging tree, and the publication rename all go
    through ``parent_fd``, so an ancestor swapped for a symlink after the
    static destination check can no longer redirect any of those writes.
    """
        parent = out_dir.parent
        parent_fd = self.api._create_pinned_parent(parent, out_dir)
        stem = out_dir.name or 'oracle-run'
        lock_name = f'.{stem}.oracle-generate.lock'
        try:
            try:
                descriptor = self.api._locked_lock_descriptor(lock_name, dir_fd=parent_fd)
            except (BlockingIOError, FileExistsError) as exc:
                raise FileExistsError(f'another generation owns reservation {parent / lock_name}') from exc
            try:
                exists = True
                if out_dir.name:
                    try:
                        os.lstat(out_dir.name, dir_fd=parent_fd)
                    except FileNotFoundError:
                        exists = False
                if exists:
                    raise FileExistsError(f'refusing to overwrite existing run {out_dir}')
            except BaseException:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
                os.close(descriptor)
                raise
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

    def _rename_noreplace(self, source, destination):
        """Linux atomic rename that never replaces ``destination``."""
        if not sys.platform.startswith('linux'):
            raise OSError(errno.ENOSYS, 'atomic no-replace publication is unavailable')
        libc = ctypes.CDLL(None, use_errno=True)
        renameat2 = getattr(libc, 'renameat2', None)
        if renameat2 is None:
            raise OSError(errno.ENOSYS, 'renameat2(RENAME_NOREPLACE) is unavailable')
        renameat2.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        renameat2.restype = ctypes.c_int
        result = renameat2(
            self.api.AT_FDCWD,
            os.fsencode(source),
            self.api.AT_FDCWD,
            os.fsencode(destination),
            self.api.RENAME_NOREPLACE,
        )
        if result != 0:
            error = ctypes.get_errno() or errno.EIO
            raise OSError(error, os.strerror(error), os.fspath(destination))

    def publish_noreplace(self, staging, out_dir, expected_identity=None):
        """Publish a sibling staging tree without ever replacing a destination.

    POSIX ``rename`` permits replacing an empty directory, so the reservation
    check alone cannot defend against a non-cooperating writer racing in after
    it.  Linux ``renameat2(RENAME_NOREPLACE)`` makes the publication point itself
    fail with ``EEXIST``.  Platforms/libcs without that primitive fail closed.
    """
        expected_identity = expected_identity or self.api._directory_identity(staging)
        if self.api._directory_identity(staging) != expected_identity:
            raise OSError(errno.ESTALE, 'publication source identity changed before rename')
        self.api._rename_noreplace(staging, out_dir)
        published_identity = self.api._directory_identity(out_dir)
        if published_identity != expected_identity:
            quarantine = out_dir.with_name(f".{out_dir.name or 'oracle-run'}.rejected-{secrets.token_hex(8)}")
            try:
                self.api._rename_noreplace(out_dir, quarantine)
            except OSError:
                pass
            raise OSError(errno.ESTALE, 'published directory identity did not match the authenticated staging tree')

    def _cleanup_staging(self, staging, staging_identity, parent_fd=None):
        """Quarantine failed staging for recovery without deleting any inode."""
        if staging is None or staging_identity is None:
            return
        owned_fd = None
        try:
            if parent_fd is None:
                owned_fd = os.open(staging.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
                parent_fd = owned_fd
            quarantine_owned_entry(parent_fd, staging.name, (*staging_identity, stat.S_IFDIR), 'oracle staging recovery')
        except (OSError, ComposeError) as exc:
            print(f'oracle_generate: staging retained for recovery: {exc}', file=sys.stderr)
        finally:
            if owned_fd is not None:
                os.close(owned_fd)


if __package__:
    _expose_package_sibling(__name__)
