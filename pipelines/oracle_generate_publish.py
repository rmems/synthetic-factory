"""No-replace publication and failed-staging recovery for oracle generation."""

import ctypes
import errno
import os
import secrets
import stat
import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("oracle_generate_publish")
    from .compose_contract import ComposeError
    from .compose_destination_rename import quarantine_owned_entry
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_generate_publish"
    )
    from compose_contract import ComposeError
    from compose_destination_rename import quarantine_owned_entry


class GenerationPublish:

    def __init__(self, api):
        self.api = api

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

    def _quarantine_mismatch(self, out_dir):
        """Move an unauthenticated publication aside for recovery."""
        quarantine = out_dir.with_name(f".{out_dir.name or 'oracle-run'}.rejected-{secrets.token_hex(8)}")
        try:
            self.api._rename_noreplace(out_dir, quarantine)
        except OSError:
            pass

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
            self.api._quarantine_mismatch(out_dir)
            raise OSError(errno.ESTALE, 'published directory identity did not match the authenticated staging tree')

    def _cleanup_parent_descriptor(self, staging, parent_fd):
        """A parent descriptor for recovery, opened when the caller lacks one."""
        if parent_fd is not None:
            return parent_fd, None
        owned = os.open(staging.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        return owned, owned

    def _cleanup_staging(self, staging, staging_identity, parent_fd=None):
        """Quarantine failed staging for recovery without deleting any inode."""
        if staging is None or staging_identity is None:
            return
        owned_fd = None
        try:
            parent_fd, owned_fd = self.api._cleanup_parent_descriptor(staging, parent_fd)
            quarantine_owned_entry(parent_fd, staging.name, (*staging_identity, stat.S_IFDIR), 'oracle staging recovery')
        except (OSError, ComposeError) as exc:
            print(f'oracle_generate: staging retained for recovery: {exc}', file=sys.stderr)
        finally:
            if owned_fd is not None:
                os.close(owned_fd)


if __package__:
    _expose_package_sibling(__name__)
