"""Cohesive checks extracted from oracle_validate_capture.py."""

class CaptureChecksPart2:
    def _verify_captured_file(self, snapshot, entry, path, errors):
        """Check one captured file against its manifest entry. Returns its line count."""
        actual_digest = self.api.hashlib.sha256(snapshot.body).hexdigest()
        expected_digest = entry["sha256"]
        if actual_digest != expected_digest:
            errors.append(
                f"{path}: sha256 mismatch: manifest {expected_digest}, actual {actual_digest}"
            )
        actual_count = sum(
            1 for line in self.api.io.BytesIO(snapshot.body) if line.strip()
        )
        expected_count = entry["records"]
        if actual_count != expected_count:
            errors.append(
                f"{path}: record-count mismatch: manifest {expected_count}, actual {actual_count}"
            )
        return actual_count

    def _capture_one_manifested_file(self, relative, actual, root_fd, errors):
        """Capture one manifest-declared file, or report why it cannot be read."""
        path, expected_stat = actual[relative]
        try:
            return self.api._snapshot_regular_file(
                root_fd,
                self.api._SnapshotRequest(
                    path, relative, self.api.MAX_JSONL_BYTES, expected_stat
                ),
            )
        except (OSError, ValueError, MemoryError) as exc:
            errors.append(
                f"{path}: could not capture authenticated file: "
                f"{type(exc).__name__}: {exc}"
            )
            return None

    def _capture_manifested_files(self, actual, valid_entries, root_fd, errors):
        """Capture every manifested file once, refusing aliases and oversized runs."""
        snapshots = []
        seen_inodes = set()
        captured_record_total = 0
        actual_names = set(actual) - {self.api.MANIFEST_FILENAME}
        for relative in sorted(valid_entries.keys() & actual_names):
            snapshot = self._capture_one_manifested_file(
                relative, actual, root_fd, errors
            )
            if snapshot is None:
                continue
            inode_key = (snapshot.device, snapshot.inode)
            if inode_key in seen_inodes:
                errors.append(f"{snapshot.path}: file aliases another manifest entry")
                continue
            seen_inodes.add(inode_key)
            captured_record_total += self.api._verify_captured_file(
                snapshot, valid_entries[relative], snapshot.path, errors
            )
            if captured_record_total > self.api.MAX_RUN_RECORDS:
                errors.append(
                    f"{snapshot.path}: captured record total exceeds "
                    f"{self.api.MAX_RUN_RECORDS}"
                )
                continue
            snapshots.append(snapshot)
        return snapshots

    def _run_tree_identity(self, files):
        """Comparable membership and stat evidence for one bounded enumeration."""
        return {
            relative: self.api._stat_identity_with_mode(status)
            for relative, (_path, status) in files.items()
        }

    def _verify_run_tree_unchanged(self, run_dir, root_fd, initial, errors):
        """Refuse files added, replaced, or edited while their peers were captured."""
        final, findings = self.api._enumerate_run_files(run_dir, root_fd)
        errors.extend(findings)
        if self.api._run_tree_identity(initial) != self.api._run_tree_identity(final):
            errors.append(f"{run_dir}: run tree changed during capture")

    def _authenticate_manifest_from_root(self, run_dir, root_fd):
        """Authenticate a run rooted at one already pinned directory descriptor."""
        run_dir = self.api.Path(run_dir)
        errors = []
        actual, tree_errors = self.api._enumerate_run_files(run_dir, root_fd)
        errors.extend(tree_errors)
        manifest_path = run_dir / self.api.MANIFEST_FILENAME
        manifest = self.api._load_run_manifest(run_dir, root_fd, actual, errors)

        actual_names = set(actual) - {self.api.MANIFEST_FILENAME}
        if not isinstance(manifest, dict):
            return manifest, [], errors
        entries = self.api._manifest_payload_entries(manifest, manifest_path, errors)
        if entries is None:
            return manifest, [], errors

        expected_names, valid_entries, declared_record_total = (
            self.api._manifest_file_entries(entries, manifest_path, errors)
        )
        if declared_record_total == 0:
            errors.append(f"{manifest_path}: declared run contains no records")

        self.api._manifest_membership_errors(
            expected_names, actual_names, manifest_path, errors
        )

        snapshots = self.api._capture_manifested_files(
            actual, valid_entries, root_fd, errors
        )
        self.api._verify_run_tree_unchanged(run_dir, root_fd, actual, errors)
        return manifest, snapshots, errors

    def authenticate_manifest(self, run_dir):
        """Capture and authenticate the exact manifest-declared run snapshot."""
        run_dir = self.api.Path(run_dir)
        try:
            root_fd = self.api._open_run_root(run_dir)
        except (OSError, ValueError) as exc:
            return None, [], [
                f"{run_dir}: could not pin run directory: {type(exc).__name__}: {exc}"
            ]
        try:
            return self.api._authenticate_manifest_from_root(run_dir, root_fd)
        finally:
            self.api.os.close(root_fd)
