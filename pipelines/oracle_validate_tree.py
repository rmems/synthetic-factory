"""Bounded directory enumeration using pinned, no-follow descriptors."""

import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("oracle_validate_tree")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_validate_tree"
    )


class RunTreeChecks:
    """Preserve live facade limits and callbacks while walking owned descriptors."""

    def __init__(self, api):
        self.api = api

    def _record_regular_file(self, entry_stat, relative, walk):
        """Record one regular file. True when a run-wide limit halts the walk."""
        if entry_stat.st_nlink != 1:
            walk.report(relative, "hard-linked files are not allowed in a run")
        walk.files[relative] = (walk.root / relative, entry_stat)
        walk.bytes_seen += entry_stat.st_size
        if walk.bytes_seen > self.api.MAX_RUN_BYTES:
            walk.errors.append(f"{walk.root}: run exceeds the {self.api.MAX_RUN_BYTES}-byte snapshot limit")
            return True
        if len(walk.files) > self.api.MAX_RUN_FILES:
            walk.errors.append(f"{walk.root}: run contains more than {self.api.MAX_RUN_FILES} files")
            return True
        return False

    def _push_subdirectory(self, entry, entry_stat, relative_path, walk):
        """Open a child directory without following links and queue it."""
        relative = relative_path.as_posix()
        if len(relative_path.parts) > self.api.MAX_RUN_DEPTH:
            walk.report(relative, f"run nesting exceeds {self.api.MAX_RUN_DEPTH} directories")
            return
        flags = (
            self.api.os.O_RDONLY
            | getattr(self.api.os, "O_CLOEXEC", 0)
            | getattr(self.api.os, "O_DIRECTORY", 0)
            | getattr(self.api.os, "O_NOFOLLOW", 0)
        )
        try:
            child_fd, child_stat = self._open_child(entry.name, flags, walk.directory_fd)
        except OSError as exc:
            walk.report(relative, f"could not open directory safely: {type(exc).__name__}")
            return
        if (child_stat.st_dev, child_stat.st_ino) != (entry_stat.st_dev, entry_stat.st_ino):
            self.api.os.close(child_fd)
            walk.report(relative, "directory changed during enumeration")
            return
        walk.stack.append((relative_path, child_fd))

    def _open_child(self, name, flags, parent_fd):
        descriptor = self.api.os.open(name, flags, dir_fd=parent_fd)
        try:
            status = self.api.os.fstat(descriptor)
        except BaseException:
            self.api.os.close(descriptor)
            raise
        return descriptor, status

    def _scan_entry(self, entry, relative_path, walk):
        """Classify one directory entry. True when a run-wide limit halts the walk."""
        relative = relative_path.as_posix()
        try:
            entry_stat = entry.stat(follow_symlinks=False)
        except OSError as exc:
            walk.report(relative, f"could not inspect entry: {type(exc).__name__}")
            return False
        if self.api.stat.S_ISLNK(entry_stat.st_mode):
            walk.report(relative, "symbolic links are not allowed in a run")
            return False
        if self.api.stat.S_ISDIR(entry_stat.st_mode):
            self.api._push_subdirectory(entry, entry_stat, relative_path, walk)
            return False
        if self.api.stat.S_ISREG(entry_stat.st_mode):
            return self.api._record_regular_file(entry_stat, relative, walk)
        walk.report(relative, "only regular files and directories are allowed")
        return False

    def _scan_directory(self, prefix, directory_fd, walk):
        """Scan one directory level. True when a run-wide limit halts the walk."""
        walk.directory_fd = directory_fd
        entries = self._bounded_entries(directory_fd, walk)
        if entries is None:
            return True
        entries.sort(key=lambda entry: entry.name)
        for entry in entries:
            if self.api._scan_entry(entry, prefix / entry.name, walk):
                return True
        return False

    def _bounded_entries(self, directory_fd, walk):
        # Enforce the entry cap while draining the iterator: sorting first would
        # materialize an untrusted directory of arbitrary size before the cap
        # could refuse it, so the walk never holds more than the cap allows.
        entries = []
        with self.api.os.scandir(directory_fd) as iterator:
            for entry in iterator:
                walk.entries_seen += 1
                if walk.entries_seen > self.api.MAX_RUN_ENTRIES:
                    walk.errors.append(
                        f"{walk.root}: run contains more than {self.api.MAX_RUN_ENTRIES} entries"
                    )
                    return None
                entries.append(entry)
        return entries

    def _enumerate_run_files(self, run_dir, root_fd):
        """List one opened run tree without following directory links."""
        walk = self.api._RunTreeWalk(root=self.api.Path(run_dir))
        # A duplicated fd shares the directory stream/cache of the first scan.
        # Reopen the same pinned inode for a fresh enumeration after mutations.
        try:
            fresh_root = self.api.os.open(".", self.api.os.O_RDONLY | self.api.os.O_DIRECTORY | self.api.os.O_CLOEXEC, dir_fd=root_fd)
        except OSError as exc:
            return {}, [f"{run_dir}: could not reopen pinned directory: {type(exc).__name__}"]
        walk.stack.append((self.api.PurePosixPath(), fresh_root))
        try:
            while walk.stack:
                prefix, directory_fd = walk.stack.pop()
                halted = self._scan_owned_directory(prefix, directory_fd, walk)
                if halted:
                    return walk.files, walk.errors
        finally:
            for _prefix, descriptor in walk.stack:
                self.api.os.close(descriptor)
        return walk.files, walk.errors

    def _scan_owned_directory(self, prefix, descriptor, walk):
        try:
            return self.api._scan_directory(prefix, descriptor, walk)
        except OSError as exc:
            walk.errors.append(
                f"{walk.root / prefix}: could not enumerate directory: {type(exc).__name__}"
            )
            return False
        finally:
            self.api.os.close(descriptor)


if __package__:
    _expose_package_sibling(__name__)
