#!/usr/bin/env python3
"""Validate a directory of oracle-grounded records (issue #77).

Fails closed. A record is an error when its envelope is wrong, when its hashes
do not cover what it stores, when its result is missing or not attributed to
the oracle it declares, or when it claims a verdict it does not earn. A record
that honestly reports its own rejection is counted, not treated as an error.

Prints totals JSON on stdout and findings on stderr. Writes nothing.

Usage:
  python3 pipelines/oracle_validate.py [options] <run_dir>

Options:
  --family NAME       Only validate this family (repeatable).
  --require-runtime   Treat reference-oracle records as errors.
  --reproduce         Re-run each oracle and compare the measurement hash.
  --max-findings N    Stop printing findings after N lines (default 50).
"""

import argparse
import hashlib
import io as io
import json
import math
import os
import re
import stat
import sys
from collections import Counter
from dataclasses import dataclass, field, replace
from pathlib import Path, PurePosixPath

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("oracle_validate")
    from . import oracle_validate_records as _oracle_validate_records
    from . import oracle_validate_tree as _oracle_validate_tree
    from . import oracle_validate_manifest as _oracle_validate_manifest
    from . import oracle_validate_manifest_records as _oracle_validate_manifest_records
    from .oracle_grounded import canon as canon, families, oracles, record
    from .oracle_grounded.rng import MAX_SEED as MAX_SEED, seed_from_label as seed_from_label
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_validate"
    )
    import oracle_validate_records as _oracle_validate_records
    import oracle_validate_tree as _oracle_validate_tree
    import oracle_validate_manifest as _oracle_validate_manifest
    import oracle_validate_manifest_records as _oracle_validate_manifest_records
    from oracle_grounded import canon as canon, families, oracles, record
    from oracle_grounded.rng import MAX_SEED as MAX_SEED, seed_from_label as seed_from_label


MANIFEST_FILENAME = "manifest.json"
MAX_MANIFEST_BYTES = 8 * 1024 * 1024
MAX_JSONL_BYTES = 64 * 1024 * 1024
MAX_RUN_FILES = 10_000
MAX_RUN_ENTRIES = 20_000
MAX_RUN_DEPTH = 32
MAX_RUN_BYTES = 128 * 1024 * 1024
MAX_RUN_RECORDS = 100_000
MAX_ROUND = 99_999_999
READ_CHUNK_BYTES = 1024 * 1024
# Exactly the keys oracle_generate.build_manifest writes. The manifest is
# canonical run metadata covered by no other digest, so its vocabulary is
# closed against undeclared provenance claims.
MANIFEST_ALLOWED_KEYS = frozenset(
    {
        "schema",
        "round",
        "seed",
        "count_per_family",
        "families",
        "oracle_commit",
        "oracle_dirty",
        "module_digest",
        "oracle_availability",
        "files",
        "generation_errors",
        "note",
    }
)
# Exactly the two notes oracle_generate.build_manifest derives from record
# publishability. The note is a provenance claim, not free text, so it is
# recomputed from the captured records rather than trusted: a manifest may
# not assert publishability its own records do not carry.
MANIFEST_NOTE_PUBLISHABLE = (
    "Counts describe this run only. Some records are publishable: they "
    "were measured by the in-repo reference simulator at the current "
    "module digest (#171) or through the named-runtime protocol; check "
    "each record's own validation.publishable and "
    "validation.publishable_reason for the authoritative per-record "
    "determination."
)
MANIFEST_NOTE_UNPUBLISHABLE = (
    "Counts describe this run only; no record here is publishable. Each "
    "record's own validation.publishable_reason states why: a validation "
    "failure, a module digest the current sources cannot reproduce, or "
    "unresolved commit or dirty state."
)


@dataclass(frozen=True)
class FileSnapshot:
    """One authenticated regular file captured exactly once."""

    path: Path
    relative: str
    body: bytes | bytearray
    device: int
    inode: int


@dataclass(frozen=True)
class _SnapshotRequest:
    path: Path
    relative: str
    limit: int
    expected_stat: object


@dataclass(frozen=True)
class ParsedRecord:
    """A parsed record plus the captured file coordinate that supplied it."""

    item: dict
    where: str
    relative: str
    verdict: str | None


class DuplicateJsonKey(ValueError):
    """A JSON object repeated a key and was therefore ambiguous."""


def _object_from_pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateJsonKey(f"duplicate JSON key {key!r}")
        value[key] = item
    return value


def _reject_constant(value):
    raise ValueError(f"non-finite JSON token {value!r}")


def _parse_finite_float(text):
    """parse_constant only sees the bare NaN/Infinity tokens; a numeric
    literal that merely overflows to inf (1e400) must be refused here."""
    parsed = float(text)
    if not math.isfinite(parsed):
        raise ValueError(f"JSON numeric literal is not finitely representable: {text}")
    return parsed


def strict_json_loads(text):
    value = json.loads(
        text,
        object_pairs_hook=_object_from_pairs,
        parse_constant=_reject_constant,
        parse_float=_parse_finite_float,
    )
    return value


def _manifest_path_text(value):
    return isinstance(value, str) and bool(value) and "\\" not in value


def _relative_manifest_parts(path):
    return not path.is_absolute() and all(part not in ("", ".", "..") for part in path.parts)


def _safe_manifest_path(value):
    if not _manifest_path_text(value):
        return None
    path = PurePosixPath(value)
    if not _relative_manifest_parts(path):
        return None
    if path.as_posix() != value or path.suffix != ".jsonl":
        return None
    return path


def _plain_int(value, *, minimum=None, maximum=None):
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and (minimum is None or value >= minimum)
        and (maximum is None or value <= maximum)
    )


def _open_beneath(root_fd, relative):
    """Open one regular-file candidate without following any path component."""
    parts = PurePosixPath(relative).parts
    if not parts or any(part in ("", ".", "..") for part in parts):
        raise ValueError("snapshot path is not a safe relative path")
    directory_fd = os.dup(root_fd)
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        for part in parts[:-1]:
            next_fd = os.open(part, directory_flags, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = next_fd
        file_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        return os.open(parts[-1], file_flags, dir_fd=directory_fd)
    finally:
        os.close(directory_fd)


def _stat_identity(status):
    """The fields that must not change while a file's bytes are captured."""
    return (
        status.st_dev,
        status.st_ino,
        status.st_size,
        status.st_mtime_ns,
        status.st_ctime_ns,
        status.st_nlink,
    )


def _stat_identity_with_mode(status):
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


def _read_within_limit(descriptor, limit):
    """Read a descriptor to EOF, refusing anything past ``limit`` bytes."""
    body = bytearray()
    captured = 0
    while True:
        chunk = os.read(descriptor, min(READ_CHUNK_BYTES, limit + 1 - captured))
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


def _capture_pinned_body(descriptor, limit, expected_stat):
    """Read one pinned descriptor, proving its identity before the read."""
    before = os.fstat(descriptor)
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise ValueError("opened object is not a singly linked regular file")
    if _stat_identity_with_mode(before) != _stat_identity_with_mode(expected_stat):
        raise ValueError("file changed after run-tree enumeration")
    body = _read_within_limit(descriptor, limit)
    return body, before, os.fstat(descriptor)


def _snapshot_regular_file(root_fd, request):
    """Capture one root-relative path once and detect identity or byte changes."""
    path = Path(request.path)
    if request.expected_stat.st_size > request.limit:
        raise ValueError(f"file exceeds the {request.limit}-byte snapshot limit")
    descriptor = _open_beneath(root_fd, request.relative)
    try:
        body, before, after = _capture_pinned_body(
            descriptor, request.limit, request.expected_stat
        )
    finally:
        os.close(descriptor)
    if _stat_identity(before) != _stat_identity(after):
        raise ValueError("file changed while its bytes were captured")
    if len(body) != after.st_size:
        raise ValueError("captured byte count does not match the regular-file size")
    return FileSnapshot(
        path=path,
        relative=request.relative,
        body=body,
        device=after.st_dev,
        inode=after.st_ino,
    )


@dataclass
class _RunTreeWalk:
    """Accumulated state for one depth-first run-tree enumeration.

    ``stack`` owns an open descriptor per queued directory; the caller is
    responsible for closing whatever remains on it.
    """

    root: Path
    stack: list = field(default_factory=list)
    files: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)
    entries_seen: int = 0
    bytes_seen: int = 0
    directory_fd: int = -1

    def report(self, relative, message):
        """Record one finding against a run-relative path."""
        self.errors.append(f"{self.root / relative}: {message}")


def _record_regular_file(entry_stat, relative, walk):
    return _oracle_validate_tree.RunTreeChecks(sys.modules[__name__])._record_regular_file(entry_stat, relative, walk)


def _push_subdirectory(entry, entry_stat, relative_path, walk):
    return _oracle_validate_tree.RunTreeChecks(sys.modules[__name__])._push_subdirectory(entry, entry_stat, relative_path, walk)


def _scan_entry(entry, relative_path, walk):
    return _oracle_validate_tree.RunTreeChecks(sys.modules[__name__])._scan_entry(entry, relative_path, walk)


def _scan_directory(prefix, directory_fd, walk):
    return _oracle_validate_tree.RunTreeChecks(sys.modules[__name__])._scan_directory(prefix, directory_fd, walk)


def _enumerate_run_files(run_dir, root_fd):
    return _oracle_validate_tree.RunTreeChecks(sys.modules[__name__])._enumerate_run_files(run_dir, root_fd)


def _open_run_root(run_dir):
    """Open and pin a real run directory without accepting a root symlink."""
    root = Path(run_dir)
    before = os.lstat(root)
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
        raise ValueError("run directory must be a real directory, not a link")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    descriptor = os.open(root, flags)
    try:
        opened = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise ValueError("run directory changed while it was opened")
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


def _is_sha256_hex(value):
    """Whether ``value`` is a bare lowercase 64-character hex digest."""
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _load_run_manifest(run_dir, root_fd, actual, errors):
    """Snapshot and parse the run manifest, or report why it cannot be read."""
    manifest_path = run_dir / MANIFEST_FILENAME
    manifest_entry = actual.get(MANIFEST_FILENAME)
    if manifest_entry is None:
        errors.append(f"{manifest_path}: required run manifest is missing")
        return None
    try:
        manifest_file, manifest_stat = manifest_entry
        manifest_snapshot = _snapshot_regular_file(
            root_fd,
            _SnapshotRequest(
                manifest_file, MANIFEST_FILENAME, MAX_MANIFEST_BYTES, manifest_stat
            ),
        )
        return strict_json_loads(manifest_snapshot.body)
    except (
        OSError,
        ValueError,
        RecursionError,
        MemoryError,
    ) as exc:
        errors.append(f"{manifest_path}: invalid manifest snapshot: {type(exc).__name__}: {exc}")
        return None


def _manifest_file_entries(entries, manifest_path, errors):
    """Validate the manifest files block.

    Returns the declared names, the entries that survived every check, and
    the declared record total.
    """
    expected_names = set()
    valid_entries = {}
    declared_record_total = 0
    for relative, entry in entries.items():
        if _safe_manifest_path(relative) is None:
            errors.append(f"{manifest_path}: unsafe manifest file path {relative!r}")
            continue
        expected_names.add(relative)
        if not isinstance(entry, dict):
            errors.append(f"{manifest_path}: files[{relative!r}] must be an object")
            continue
        unknown = sorted(set(entry) - {"sha256", "records"})
        if unknown:
            # Generation writes exactly these two fields; anything else is an
            # unauthenticated provenance claim riding on canonical metadata.
            errors.append(
                f"{manifest_path}: files[{relative!r}] carries unauthenticated "
                "sibling keys: " + ", ".join(unknown)
            )
            continue
        if not _is_sha256_hex(entry.get("sha256")):
            errors.append(f"{manifest_path}: files[{relative!r}].sha256 is invalid")
            continue
        count = entry.get("records")
        if not _plain_int(count, minimum=0, maximum=MAX_RUN_RECORDS):
            errors.append(f"{manifest_path}: files[{relative!r}].records is invalid")
            continue
        declared_record_total += count
        if declared_record_total > MAX_RUN_RECORDS:
            errors.append(f"{manifest_path}: declared record total exceeds {MAX_RUN_RECORDS}")
            continue
        valid_entries[relative] = entry
    return expected_names, valid_entries, declared_record_total


def _verify_captured_file(snapshot, entry, path, errors):
    """Check one captured file against its manifest entry. Returns its line count."""
    actual_digest = hashlib.sha256(snapshot.body).hexdigest()
    expected_digest = entry["sha256"]
    if actual_digest != expected_digest:
        errors.append(
            f"{path}: sha256 mismatch: manifest {expected_digest}, actual {actual_digest}"
        )
    actual_count = sum(1 for line in io.BytesIO(snapshot.body) if line.strip())
    expected_count = entry["records"]
    if actual_count != expected_count:
        errors.append(
            f"{path}: record-count mismatch: manifest {expected_count}, actual {actual_count}"
        )
    return actual_count


def _capture_manifested_files(actual, valid_entries, root_fd, errors):
    """Capture every manifested file once, refusing aliases and oversized runs."""
    snapshots = []
    seen_inodes = set()
    captured_record_total = 0
    actual_names = set(actual) - {MANIFEST_FILENAME}
    for relative in sorted(valid_entries.keys() & actual_names):
        path, expected_stat = actual[relative]
        try:
            snapshot = _snapshot_regular_file(
                root_fd,
                _SnapshotRequest(path, relative, MAX_JSONL_BYTES, expected_stat),
            )
        except (OSError, ValueError, MemoryError) as exc:
            errors.append(
                f"{path}: could not capture authenticated file: {type(exc).__name__}: {exc}"
            )
            continue
        inode_key = (snapshot.device, snapshot.inode)
        if inode_key in seen_inodes:
            errors.append(f"{path}: file aliases another manifest entry")
            continue
        seen_inodes.add(inode_key)
        captured_record_total += _verify_captured_file(
            snapshot, valid_entries[relative], path, errors
        )
        if captured_record_total > MAX_RUN_RECORDS:
            errors.append(f"{path}: captured record total exceeds {MAX_RUN_RECORDS}")
            continue
        snapshots.append(snapshot)
    return snapshots


def _run_tree_identity(files):
    """Comparable membership and stat evidence for one bounded enumeration."""
    return {
        relative: _stat_identity_with_mode(status)
        for relative, (_path, status) in files.items()
    }


def _verify_run_tree_unchanged(run_dir, root_fd, initial, errors):
    """Refuse files added, replaced, or edited while their peers were captured."""
    final, findings = _enumerate_run_files(run_dir, root_fd)
    errors.extend(findings)
    if _run_tree_identity(initial) != _run_tree_identity(final):
        errors.append(f"{run_dir}: run tree changed during capture")


def _manifest_payload_entries(manifest, manifest_path, errors):
    if manifest.get("schema") != record.SCHEMA_ID:
        errors.append(
            f"{manifest_path}: schema must be {record.SCHEMA_ID!r}, got {manifest.get('schema')!r}"
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


def _manifest_membership_errors(expected_names, actual_names, manifest_path, errors):
    for relative in sorted(expected_names - actual_names):
        errors.append(f"{manifest_path}: manifest file is missing: {relative}")
    for relative in sorted(actual_names - expected_names):
        errors.append(f"{manifest_path}: unmanifested file is present: {relative}")


def _authenticate_manifest_from_root(run_dir, root_fd):
    """Authenticate a run rooted at one already pinned directory descriptor."""
    run_dir = Path(run_dir)
    errors = []
    actual, tree_errors = _enumerate_run_files(run_dir, root_fd)
    errors.extend(tree_errors)
    manifest_path = run_dir / MANIFEST_FILENAME
    manifest = _load_run_manifest(run_dir, root_fd, actual, errors)

    actual_names = set(actual) - {MANIFEST_FILENAME}
    if not isinstance(manifest, dict):
        return manifest, [], errors
    entries = _manifest_payload_entries(manifest, manifest_path, errors)
    if entries is None:
        return manifest, [], errors

    expected_names, valid_entries, declared_record_total = _manifest_file_entries(
        entries, manifest_path, errors
    )
    if declared_record_total == 0:
        errors.append(f"{manifest_path}: declared run contains no records")

    _manifest_membership_errors(expected_names, actual_names, manifest_path, errors)

    snapshots = _capture_manifested_files(actual, valid_entries, root_fd, errors)
    _verify_run_tree_unchanged(run_dir, root_fd, actual, errors)
    return manifest, snapshots, errors


def authenticate_manifest(run_dir):
    """Capture and authenticate the exact manifest-declared run snapshot."""
    run_dir = Path(run_dir)
    try:
        root_fd = _open_run_root(run_dir)
    except (OSError, ValueError) as exc:
        return None, [], [f"{run_dir}: could not pin run directory: {type(exc).__name__}: {exc}"]
    try:
        return _authenticate_manifest_from_root(run_dir, root_fd)
    finally:
        os.close(root_fd)


def parse_args(argv):
    parser = argparse.ArgumentParser(add_help=True, description=__doc__)
    parser.add_argument("run_dir", nargs="?")
    parser.add_argument("--family", action="append", dest="family_names")
    parser.add_argument("--oracle-rust-bin", help="prebuilt native oracle executable; implies replay")
    parser.add_argument("--require-runtime", action="store_true")
    parser.add_argument("--reproduce", action="store_true")
    parser.add_argument("--max-findings", type=int, default=50)
    return parser.parse_args(argv)


@dataclass(frozen=True)
class _FileScope:
    """Per-file state shared by the steps that validate one record."""

    path: object
    relative: str
    require_runtime: bool
    reproduce: bool
    selected: object
    totals: object
    errors: list
    seen_ids: dict
    expected_commit: object = None

    def report(self, where, message):
        """Record one finding against a file coordinate."""
        self.errors.append(f"{where}: {message}")


def _verdict_for_file(name):
    return _oracle_validate_records.RecordChecks(sys.modules[__name__])._verdict_for_file(name)


def _parse_record_line(line, where, scope):
    return _oracle_validate_records.RecordChecks(sys.modules[__name__])._parse_record_line(line, where, scope)


def _duplicate_id_finding(item, where, seen_ids):
    return _oracle_validate_records.RecordChecks(sys.modules[__name__])._duplicate_id_finding(item, where, seen_ids)


def _classify_layers(item, require_runtime, expected_commit=None):
    return _oracle_validate_records.RecordChecks(sys.modules[__name__])._classify_layers(item, require_runtime, expected_commit)


def _fatal_findings(item, layers, identity_finding, scope):
    return _oracle_validate_records.RecordChecks(sys.modules[__name__])._fatal_findings(item, layers, identity_finding, scope)


def _count_valid_record(item, layers, totals):
    return _oracle_validate_records.RecordChecks(sys.modules[__name__])._count_valid_record(item, layers, totals)


def _reproduce_record(item, where, scope):
    return _oracle_validate_records.RecordChecks(sys.modules[__name__])._reproduce_record(item, where, scope)


def _validate_one_record(item, where, scope):
    return _oracle_validate_records.RecordChecks(sys.modules[__name__])._validate_one_record(item, where, scope)


def validate_file(snapshot, require_runtime, reproduce, selected, seen_ids=None, expected_commit=None):
    """Validate one captured JSONL snapshot. Returns totals, errors, records.

    ``expected_commit`` is the run manifest's already-resolved oracle commit;
    when provided, a record stamped with a different commit is rejected by
    string comparison instead of launching its own repository resolution, so
    a run full of distinct forged commits cannot hold the CLI in git.
    """
    scope = _FileScope(
        path=snapshot.path,
        relative=snapshot.relative,
        require_runtime=require_runtime,
        reproduce=reproduce,
        selected=selected,
        totals=Counter(),
        errors=[],
        seen_ids={} if seen_ids is None else seen_ids,
        expected_commit=expected_commit,
    )
    return _oracle_validate_records.RecordChecks(sys.modules[__name__]).validate_file(snapshot, scope)


_RUN_FILE_RE = re.compile(
    r"^(?P<family>[^/]+)/(?P<verdict>accepted|rejected)-r"
    r"(?P<round>[0-9]{1,8})\.jsonl$"
)


def _summary(records, manifest_path, label, errors):
    return _oracle_validate_manifest_records.ManifestRecordChecks(sys.modules[__name__])._summary(records, manifest_path, label, errors)


@dataclass(frozen=True)
class _ManifestHeader:
    """The manifest scalars that every metadata phase binds records against."""

    round_number: object
    master_seed: object
    count_per_family: object
    commit: object
    dirty: object
    module_digest: object

    @property
    def round_ok(self):
        """Whether ``round`` is usable as a comparison key."""
        return _plain_int(self.round_number, minimum=1, maximum=MAX_ROUND)

    @property
    def count_ok(self):
        """Whether ``count_per_family`` is usable as a comparison key."""
        return _plain_int(self.count_per_family, minimum=1, maximum=MAX_RUN_RECORDS)


@dataclass(frozen=True)
class _MetadataContext:
    """State threaded through the manifest metadata phases.

    ``errors`` and ``probe_values`` are deliberately shared mutable objects:
    every phase appends to the one findings list, in order, so the order a
    reader sees is the order the rules ran.
    """

    header: _ManifestHeader
    manifest_path: object
    errors: list
    probe_values: dict
    family: str = ""

    def report(self, message):
        """Record one finding against the manifest."""
        self.errors.append(f"{self.manifest_path}: {message}")

    def bound(self, family):
        """A view of this context scoped to one family."""
        return replace(self, family=family)


def _read_manifest_header(manifest):
    return _oracle_validate_manifest.ManifestChecks(sys.modules[__name__])._read_manifest_header(manifest)


def _header_field_errors(context):
    return _oracle_validate_manifest.ManifestChecks(sys.modules[__name__])._header_field_errors(context)


def _declared_families_block(manifest, context):
    return _oracle_validate_manifest.ManifestChecks(sys.modules[__name__])._declared_families_block(manifest, context)


def _run_file_layout(snapshots, context):
    return _oracle_validate_manifest.ManifestChecks(sys.modules[__name__])._run_file_layout(snapshots, context)


def _family_file_pairing_errors(file_info, actual_families, context):
    return _oracle_validate_manifest.ManifestChecks(sys.modules[__name__])._family_file_pairing_errors(file_info, actual_families, context)


def _record_index(parsed, context):
    return _oracle_validate_manifest_records.ManifestRecordChecks(sys.modules[__name__])._record_index(parsed, context)


def _record_oracle_binding_errors(parsed, oracle, index, context):
    return _oracle_validate_manifest_records.ManifestRecordChecks(sys.modules[__name__])._record_oracle_binding_errors(parsed, oracle, index, context)


def _record_seed_errors(parsed, oracle, index, context):
    return _oracle_validate_manifest_records.ManifestRecordChecks(sys.modules[__name__])._record_seed_errors(parsed, oracle, index, context)


def _record_availability_errors(parsed, oracle, context):
    return _oracle_validate_manifest_records.ManifestRecordChecks(sys.modules[__name__])._record_availability_errors(parsed, oracle, context)


def _collect_rejection_reasons(parsed, reasons, context):
    return _oracle_validate_manifest_records.ManifestRecordChecks(sys.modules[__name__])._collect_rejection_reasons(parsed, reasons, context)


def _indexes_are_complete(indexes, context):
    return _oracle_validate_manifest_records.ManifestRecordChecks(sys.modules[__name__])._indexes_are_complete(indexes, context)


def _family_summary(family, records, context):
    return _oracle_validate_manifest_records.ManifestRecordChecks(sys.modules[__name__])._family_summary(family, records, context)


def _group_records_by_family(parsed_records, file_info, actual_families):
    return _oracle_validate_manifest_records.ManifestRecordChecks(sys.modules[__name__])._group_records_by_family(parsed_records, file_info, actual_families)


def _expected_runtime_set(actual_families):
    return _oracle_validate_manifest.ManifestChecks(sys.modules[__name__])._expected_runtime_set(actual_families)


def _availability_probe_errors(probes, context):
    return _oracle_validate_manifest.ManifestChecks(sys.modules[__name__])._availability_probe_errors(probes, context)


def _availability_rollup_errors(availability, probes, runtime_names, context):
    return _oracle_validate_manifest.ManifestChecks(sys.modules[__name__])._availability_rollup_errors(availability, probes, runtime_names, context)


def _availability_block_errors(manifest, actual_families, context):
    return _oracle_validate_manifest.ManifestChecks(sys.modules[__name__])._availability_block_errors(manifest, actual_families, context)


def _manifest_metadata_errors(manifest, snapshots, parsed_records, run_dir):
    return _oracle_validate_manifest.ManifestChecks(sys.modules[__name__])._manifest_metadata_errors(manifest, snapshots, parsed_records, run_dir)


def _manifest_note_errors(manifest, parsed_records, context):
    return _oracle_validate_manifest.ManifestChecks(sys.modules[__name__])._manifest_note_errors(manifest, parsed_records, context)


def validate_run(run_dir, require_runtime=False, reproduce=False, selected=(), *, oracle_rust_bin=None):
    if __package__:
        from .oracle_grounded.native_gate import runtime_gate
    else:
        from oracle_grounded.native_gate import runtime_gate
    with runtime_gate(oracle_rust_bin):
        return validate_run_snapshot(
            run_dir, authenticate_manifest(run_dir),
            options=RunValidationOptions(
                require_runtime, reproduce or oracle_rust_bin is not None, selected,
            ),
        )


def _snapshot_expected_commit(manifest):
    # Resolve the manifest's oracle commit once; per-record validation then
    # binds each record to it by string comparison rather than resolving
    # every distinct stamped commit against the repository. The binding is
    # kept even when the manifest commit is invalid or missing -- an empty
    # sentinel then mismatches every record -- so a malformed run cannot
    # regain per-record repository lookups by breaking its own manifest.
    expected_commit = None
    if isinstance(manifest, dict):
        manifest_commit = manifest.get("oracle_commit")
        if isinstance(manifest_commit, str) and manifest_commit:
            expected_commit = manifest_commit
            if oracles.is_source_commit(manifest_commit):
                # One resolution for the whole run; a definitive miss is
                # negatively cached, so matching records add no lookups.
                oracles.resolve_source_commit(manifest_commit)
        else:
            expected_commit = ""
    return expected_commit


def _snapshot_metadata_errors(run_dir, manifest, snapshots, parsed_records):
    metadata_errors = []
    if isinstance(manifest, dict):
        try:
            metadata_errors = _manifest_metadata_errors(
                manifest, snapshots, parsed_records, run_dir
            )
        except Exception as exc:  # final boundary around untrusted manifest data
            metadata_errors = [
                f"{Path(run_dir) / 'manifest.json'}: manifest metadata validation "
                f"raised an internal exception: {type(exc).__name__}"
            ]
    return metadata_errors


@dataclass(frozen=True)
class RunValidationOptions:
    require_runtime: bool = False
    reproduce: bool = False
    selected: tuple = ()


def validate_run_snapshot(run_dir, authentication, *, options=None):
    """Validate the same authenticated bytes retained by a source consumer."""
    manifest, snapshots, manifest_errors = authentication
    options = options or RunValidationOptions()
    totals = Counter()
    errors = []
    by_family = Counter()
    errors.extend(manifest_errors)
    expected_commit = _snapshot_expected_commit(manifest)
    seen_ids = {}
    parsed_records = []
    for snapshot in snapshots:
        file_totals, file_errors, file_records = validate_file(
            snapshot,
            options.require_runtime,
            options.reproduce,
            options.selected,
            seen_ids=seen_ids,
            expected_commit=expected_commit,
        )
        totals.update(file_totals)
        errors.extend(file_errors)
        parsed_records.extend(file_records)
        if file_totals["records"]:
            # Skip zero entries so a --family filter reports only what it kept.
            by_family[snapshot.path.parent.name] += file_totals["records"]
    metadata_errors = _snapshot_metadata_errors(run_dir, manifest, snapshots, parsed_records)
    errors.extend(metadata_errors)
    report = {
        "run_dir": str(Path(run_dir).resolve()),
        "files": len(snapshots),
        "manifest_valid": not (manifest_errors or metadata_errors),
        "records": totals["records"],
        "accepted": totals["accepted"],
        "rejected": totals["rejected"],
        "invalid": totals["invalid"],
        "parse_failures": totals["parse_failures"],
        "skipped": totals["skipped"],
        "reference_oracle": totals["reference_oracle"],
        "named_runtime": totals["named_runtime"],
        "mixed_oracle": totals["mixed_oracle"],
        "publishable": totals["publishable"],
        "by_family": dict(sorted(by_family.items())),
    }
    if options.reproduce:
        report["reproduce"] = {
            key.removeprefix("reproduce_"): value
            for key, value in sorted(totals.items())
            if key.startswith("reproduce_")
        }
    return report, errors


def main(argv=None):
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    if not args.run_dir:
        print("oracle_validate: a run directory is required", file=sys.stderr)
        return 2
    run_dir = Path(args.run_dir)
    if not run_dir.is_dir():
        print(f"oracle_validate: not a directory: {run_dir}", file=sys.stderr)
        return 2
    selected = set(args.family_names or ())
    unknown = sorted(selected - set(families.SPECS))
    if unknown:
        print(f"oracle_validate: unknown families: {', '.join(unknown)}", file=sys.stderr)
        return 2

    try:
        report, errors = validate_run(
            run_dir,
            require_runtime=args.require_runtime,
            reproduce=args.reproduce,
            selected=selected,
            oracle_rust_bin=args.oracle_rust_bin,
        )
    except (OSError, ValueError) as exc:
        print(f"oracle_validate: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    finding_limit = max(0, args.max_findings)
    for finding in errors[:finding_limit]:
        print(finding, file=sys.stderr)
    hidden = max(0, len(errors) - finding_limit)
    if hidden:
        print(f"... {hidden} more findings", file=sys.stderr)
    return 1 if errors else 0


if __package__:
    _expose_package_sibling(__name__)


if __name__ == "__main__":
    sys.exit(main())
