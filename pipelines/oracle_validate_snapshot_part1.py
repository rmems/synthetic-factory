"""Cohesive checks extracted from oracle_validate_snapshot.py."""

class SnapshotChecksPart1:
    def _open_beneath(self, root_fd, relative):
        """Open one regular-file candidate without following any path component."""
        parts = self.api.PurePosixPath(relative).parts
        if not parts or any(part in ("", ".", "..") for part in parts):
            raise ValueError("snapshot path is not a safe relative path")
        directory_fd = self.api.os.dup(root_fd)
        directory_flags = (
            self.api.os.O_RDONLY
            | getattr(self.api.os, "O_CLOEXEC", 0)
            | getattr(self.api.os, "O_DIRECTORY", 0)
            | getattr(self.api.os, "O_NOFOLLOW", 0)
        )
        try:
            for part in parts[:-1]:
                next_fd = self.api.os.open(part, directory_flags, dir_fd=directory_fd)
                self.api.os.close(directory_fd)
                directory_fd = next_fd
            file_flags = (
                self.api.os.O_RDONLY
                | getattr(self.api.os, "O_CLOEXEC", 0)
                | getattr(self.api.os, "O_NOFOLLOW", 0)
            )
            return self.api.os.open(parts[-1], file_flags, dir_fd=directory_fd)
        finally:
            self.api.os.close(directory_fd)

    def _stat_identity(self, status):
        """The fields that must not change while a file's bytes are captured."""
        return (
            status.st_dev,
            status.st_ino,
            status.st_size,
            status.st_mtime_ns,
            status.st_ctime_ns,
            status.st_nlink,
        )

    def _stat_identity_with_mode(self, status):
        """``_stat_identity`` plus the mode, for the pre-read enumeration check."""
        return (
            status.st_dev,
            status.st_ino,
            status.st_mode,
            status.st_size,
            status.st_mtime_ns,
            status.st_ctime_ns,
            status.st_nlink,
        )

    def _open_run_root(self, run_dir):
        """Open and pin a real run directory without accepting a root symlink."""
        root = self.api.Path(run_dir)
        before = self.api.os.lstat(root)
        if self.api.stat.S_ISLNK(before.st_mode) or not self.api.stat.S_ISDIR(
            before.st_mode
        ):
            raise ValueError("run directory must be a real directory, not a link")
        flags = (
            self.api.os.O_RDONLY
            | getattr(self.api.os, "O_CLOEXEC", 0)
            | getattr(self.api.os, "O_DIRECTORY", 0)
            | getattr(self.api.os, "O_NOFOLLOW", 0)
        )
        descriptor = self.api.os.open(root, flags)
        try:
            opened = self.api.os.fstat(descriptor)
            if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
                raise ValueError("run directory changed while it was opened")
        except BaseException:
            self.api.os.close(descriptor)
            raise
        return descriptor
