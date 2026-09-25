"""Cohesive checks extracted from oracle_validate_snapshot.py."""

class SnapshotChecksPart2:
    def _read_within_limit(self, descriptor, limit):
        """Read a descriptor to EOF, refusing anything past ``limit`` bytes."""
        body = bytearray()
        captured = 0
        while True:
            chunk = self.api.os.read(
                descriptor, min(self.api.READ_CHUNK_BYTES, limit + 1 - captured)
            )
            if not chunk:
                break
            try:
                body.extend(chunk)
            except MemoryError as exc:
                raise ValueError("snapshot allocation exceeded available memory") from exc
            captured += len(chunk)
            if captured > limit:
                raise ValueError(f"file exceeds the {limit}-byte snapshot limit")
        return body

    def _capture_pinned_body(self, descriptor, limit, expected_stat):
        """Read one pinned descriptor, proving its identity before the read."""
        before = self.api.os.fstat(descriptor)
        if not self.api.stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise ValueError("opened object is not a singly linked regular file")
        if self.api._stat_identity_with_mode(before) != self.api._stat_identity_with_mode(
            expected_stat
        ):
            raise ValueError("file changed after run-tree enumeration")
        body = self.api._read_within_limit(descriptor, limit)
        return body, before, self.api.os.fstat(descriptor)

    def _snapshot_regular_file(self, root_fd, request):
        """Capture one root-relative path once and detect identity or byte changes."""
        path = self.api.Path(request.path)
        if request.expected_stat.st_size > request.limit:
            raise ValueError(f"file exceeds the {request.limit}-byte snapshot limit")
        descriptor = self.api._open_beneath(root_fd, request.relative)
        try:
            body, before, after = self.api._capture_pinned_body(
                descriptor, request.limit, request.expected_stat
            )
        finally:
            self.api.os.close(descriptor)
        if self.api._stat_identity(before) != self.api._stat_identity(after):
            raise ValueError("file changed while its bytes were captured")
        if len(body) != after.st_size:
            raise ValueError("captured byte count does not match the regular-file size")
        return self.api.FileSnapshot(
            path=path,
            relative=request.relative,
            body=body,
            device=after.st_dev,
            inode=after.st_ino,
        )
