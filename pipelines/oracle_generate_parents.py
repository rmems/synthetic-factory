"""Open-by-descriptor run parents: missing ancestors, pinning, authentication."""

import errno
import os
from pathlib import Path
import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("oracle_generate_parents")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_generate_parents"
    )


class GenerationParents:

    def __init__(self, api):
        self.api = api

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


if __package__:
    _expose_package_sibling(__name__)
