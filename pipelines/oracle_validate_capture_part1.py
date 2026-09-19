"""Cohesive checks extracted from oracle_validate_capture.py."""

class CaptureChecksPart1:
    def _manifest_path_text(self, value):
        return isinstance(value, str) and bool(value) and "\\" not in value

    def _relative_manifest_parts(self, path):
        return not path.is_absolute() and all(
            part not in ("", ".", "..") for part in path.parts
        )

    def _safe_manifest_path(self, value):
        if not self.api._manifest_path_text(value):
            return None
        path = self.api.PurePosixPath(value)
        if not self.api._relative_manifest_parts(path):
            return None
        if path.as_posix() != value or path.suffix != ".jsonl":
            return None
        return path

    def _is_sha256_hex(self, value):
        """Whether ``value`` is a bare lowercase 64-character hex digest."""
        return (
            isinstance(value, str)
            and len(value) == 64
            and all(character in "0123456789abcdef" for character in value)
        )

    def _load_run_manifest(self, run_dir, root_fd, actual, errors):
        """Snapshot and parse the run manifest, or report why it cannot be read."""
        manifest_path = run_dir / self.api.MANIFEST_FILENAME
        manifest_entry = actual.get(self.api.MANIFEST_FILENAME)
        if manifest_entry is None:
            errors.append(f"{manifest_path}: required run manifest is missing")
            return None
        try:
            manifest_file, manifest_stat = manifest_entry
            manifest_snapshot = self.api._snapshot_regular_file(
                root_fd,
                self.api._SnapshotRequest(
                    manifest_file,
                    self.api.MANIFEST_FILENAME,
                    self.api.MAX_MANIFEST_BYTES,
                    manifest_stat,
                ),
            )
            return self.api.strict_json_loads(manifest_snapshot.body)
        except (
            OSError,
            ValueError,
            RecursionError,
            MemoryError,
        ) as exc:
            errors.append(
                f"{manifest_path}: invalid manifest snapshot: {type(exc).__name__}: {exc}"
            )
            return None

    def _manifest_file_entries(self, entries, manifest_path, errors):
        """Validate the manifest files block.

        Returns the declared names, the entries that survived every check, and
        the declared record total.
        """
        expected_names = set()
        valid_entries = {}
        declared_record_total = 0
        for relative, entry in entries.items():
            if self.api._safe_manifest_path(relative) is None:
                errors.append(f"{manifest_path}: unsafe manifest file path {relative!r}")
                continue
            expected_names.add(relative)
            if not self._manifest_entry_fields(relative, entry, manifest_path, errors):
                continue
            declared_record_total += entry["records"]
            if declared_record_total > self.api.MAX_RUN_RECORDS:
                errors.append(
                    f"{manifest_path}: declared record total exceeds "
                    f"{self.api.MAX_RUN_RECORDS}"
                )
                continue
            valid_entries[relative] = entry
        return expected_names, valid_entries, declared_record_total

    def _manifest_entry_fields(self, relative, entry, manifest_path, errors):
        """Whether one files[] entry carries exactly the authenticated fields."""
        if not isinstance(entry, dict):
            errors.append(f"{manifest_path}: files[{relative!r}] must be an object")
            return False
        unknown = sorted(set(entry) - {"sha256", "records"})
        if unknown:
            # Generation writes exactly these two fields; anything else is an
            # unauthenticated provenance claim riding on canonical metadata.
            errors.append(
                f"{manifest_path}: files[{relative!r}] carries unauthenticated "
                "sibling keys: " + ", ".join(unknown)
            )
            return False
        if not self.api._is_sha256_hex(entry.get("sha256")):
            errors.append(f"{manifest_path}: files[{relative!r}].sha256 is invalid")
            return False
        if not self.api._plain_int(
            entry.get("records"), minimum=0, maximum=self.api.MAX_RUN_RECORDS
        ):
            errors.append(f"{manifest_path}: files[{relative!r}].records is invalid")
            return False
        return True

    def _manifest_payload_entries(self, manifest, manifest_path, errors):
        if manifest.get("schema") != self.api.record.SCHEMA_ID:
            errors.append(
                f"{manifest_path}: schema must be {self.api.record.SCHEMA_ID!r}, "
                f"got {manifest.get('schema')!r}"
            )
        if manifest.get("generation_errors") != []:
            errors.append(f"{manifest_path}: generation_errors must be an empty array")
        entries = manifest.get("files")
        if not isinstance(entries, dict):
            errors.append(f"{manifest_path}: files must be an object")
            return None
        if not entries:
            errors.append(f"{manifest_path}: files must declare at least one payload")
        return entries

    def _manifest_membership_errors(self, expected_names, actual_names, manifest_path, errors):
        for relative in sorted(expected_names - actual_names):
            errors.append(f"{manifest_path}: manifest file is missing: {relative}")
        for relative in sorted(actual_names - expected_names):
            errors.append(f"{manifest_path}: unmanifested file is present: {relative}")
