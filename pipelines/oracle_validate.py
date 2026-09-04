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
import io
import json
import math
import os
import re
import stat
import sys
from collections import Counter
from dataclasses import dataclass, field, replace
from pathlib import Path, PurePosixPath

from oracle_grounded import canon, families, oracles, record
from oracle_grounded.rng import seed_from_label


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


def _safe_manifest_path(value):
    if not isinstance(value, str) or not value or "\\" in value:
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
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


def _snapshot_regular_file(root_fd, path, relative, limit, expected_stat):
    """Capture one root-relative path once and detect identity or byte changes."""
    path = Path(path)
    if expected_stat.st_size > limit:
        raise ValueError(f"file exceeds the {limit}-byte snapshot limit")
    descriptor = _open_beneath(root_fd, relative)
    try:
        body, before, after = _capture_pinned_body(descriptor, limit, expected_stat)
    finally:
        os.close(descriptor)
    if _stat_identity(before) != _stat_identity(after):
        raise ValueError("file changed while its bytes were captured")
    if len(body) != after.st_size:
        raise ValueError("captured byte count does not match the regular-file size")
    return FileSnapshot(
        path=path,
        relative=relative,
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
    """Record one regular file. True when a run-wide limit halts the walk."""
    if entry_stat.st_nlink != 1:
        walk.report(relative, "hard-linked files are not allowed in a run")
    walk.files[relative] = (walk.root / relative, entry_stat)
    walk.bytes_seen += entry_stat.st_size
    if walk.bytes_seen > MAX_RUN_BYTES:
        walk.errors.append(f"{walk.root}: run exceeds the {MAX_RUN_BYTES}-byte snapshot limit")
        return True
    if len(walk.files) > MAX_RUN_FILES:
        walk.errors.append(f"{walk.root}: run contains more than {MAX_RUN_FILES} files")
        return True
    return False


def _push_subdirectory(entry, entry_stat, relative_path, walk):
    """Open a child directory without following links and queue it."""
    relative = relative_path.as_posix()
    if len(relative_path.parts) > MAX_RUN_DEPTH:
        walk.report(relative, f"run nesting exceeds {MAX_RUN_DEPTH} directories")
        return
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        child_fd = os.open(entry.name, flags, dir_fd=walk.directory_fd)
        child_stat = os.fstat(child_fd)
    except OSError as exc:
        walk.report(relative, f"could not open directory safely: {type(exc).__name__}")
        return
    if (child_stat.st_dev, child_stat.st_ino) != (entry_stat.st_dev, entry_stat.st_ino):
        os.close(child_fd)
        walk.report(relative, "directory changed during enumeration")
        return
    walk.stack.append((relative_path, child_fd))


def _scan_entry(entry, relative_path, walk):
    """Classify one directory entry. True when a run-wide limit halts the walk."""
    relative = relative_path.as_posix()
    try:
        entry_stat = entry.stat(follow_symlinks=False)
    except OSError as exc:
        walk.report(relative, f"could not inspect entry: {type(exc).__name__}")
        return False
    if stat.S_ISLNK(entry_stat.st_mode):
        walk.report(relative, "symbolic links are not allowed in a run")
        return False
    if stat.S_ISDIR(entry_stat.st_mode):
        _push_subdirectory(entry, entry_stat, relative_path, walk)
        return False
    if stat.S_ISREG(entry_stat.st_mode):
        return _record_regular_file(entry_stat, relative, walk)
    walk.report(relative, "only regular files and directories are allowed")
    return False


def _scan_directory(prefix, directory_fd, walk):
    """Scan one directory level. True when a run-wide limit halts the walk."""
    walk.directory_fd = directory_fd
    # Enforce the entry cap while draining the iterator: sorting first would
    # materialize an untrusted directory of arbitrary size before the cap
    # could refuse it, so the walk never holds more than the cap allows.
    entries = []
    with os.scandir(directory_fd) as iterator:
        for entry in iterator:
            walk.entries_seen += 1
            if walk.entries_seen > MAX_RUN_ENTRIES:
                walk.errors.append(
                    f"{walk.root}: run contains more than {MAX_RUN_ENTRIES} entries"
                )
                return True
            entries.append(entry)
    entries.sort(key=lambda entry: entry.name)
    for entry in entries:
        if _scan_entry(entry, prefix / entry.name, walk):
            return True
    return False


def _enumerate_run_files(run_dir, root_fd):
    """List one opened run tree without following directory links."""
    walk = _RunTreeWalk(root=Path(run_dir))
    walk.stack.append((PurePosixPath(), os.dup(root_fd)))
    try:
        while walk.stack:
            prefix, directory_fd = walk.stack.pop()
            halted = False
            try:
                halted = _scan_directory(prefix, directory_fd, walk)
            except OSError as exc:
                walk.errors.append(
                    f"{walk.root / prefix}: could not enumerate directory: {type(exc).__name__}"
                )
            finally:
                os.close(directory_fd)
            if halted:
                return walk.files, walk.errors
    finally:
        for _prefix, descriptor in walk.stack:
            os.close(descriptor)
    return walk.files, walk.errors


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
    opened = os.fstat(descriptor)
    if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
        os.close(descriptor)
        raise ValueError("run directory changed while it was opened")
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
    manifest_path = run_dir / "manifest.json"
    manifest_entry = actual.get("manifest.json")
    if manifest_entry is None:
        errors.append(f"{manifest_path}: required run manifest is missing")
        return None
    try:
        manifest_file, manifest_stat = manifest_entry
        manifest_snapshot = _snapshot_regular_file(
            root_fd,
            manifest_file,
            "manifest.json",
            MAX_MANIFEST_BYTES,
            expected_stat=manifest_stat,
        )
        return strict_json_loads(manifest_snapshot.body)
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
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
    actual_names = set(actual) - {"manifest.json"}
    for relative in sorted(valid_entries.keys() & actual_names):
        path, expected_stat = actual[relative]
        try:
            snapshot = _snapshot_regular_file(
                root_fd,
                path,
                relative,
                MAX_JSONL_BYTES,
                expected_stat=expected_stat,
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


def _authenticate_manifest_from_root(run_dir, root_fd):
    """Authenticate a run rooted at one already pinned directory descriptor."""
    run_dir = Path(run_dir)
    errors = []
    actual, tree_errors = _enumerate_run_files(run_dir, root_fd)
    errors.extend(tree_errors)
    manifest_path = run_dir / "manifest.json"
    manifest = _load_run_manifest(run_dir, root_fd, actual, errors)

    actual_names = set(actual) - {"manifest.json"}
    if not isinstance(manifest, dict):
        return manifest, [], errors
    if manifest.get("schema") != record.SCHEMA_ID:
        errors.append(
            f"{manifest_path}: schema must be {record.SCHEMA_ID!r}, got {manifest.get('schema')!r}"
        )
    if manifest.get("generation_errors") != []:
        errors.append(f"{manifest_path}: generation_errors must be an empty array")
    entries = manifest.get("files")
    if not isinstance(entries, dict):
        errors.append(f"{manifest_path}: files must be an object")
        return manifest, [], errors
    if not entries:
        errors.append(f"{manifest_path}: files must declare at least one payload")

    expected_names, valid_entries, declared_record_total = _manifest_file_entries(
        entries, manifest_path, errors
    )
    if declared_record_total == 0:
        errors.append(f"{manifest_path}: declared run contains no records")

    for relative in sorted(expected_names - actual_names):
        errors.append(f"{manifest_path}: manifest file is missing: {relative}")
    for relative in sorted(actual_names - expected_names):
        errors.append(f"{manifest_path}: unmanifested file is present: {relative}")

    snapshots = _capture_manifested_files(actual, valid_entries, root_fd, errors)
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
    """The verdict a run file name reserves, or None."""
    return next(
        (verdict for verdict in ("accepted", "rejected") if name.startswith(f"{verdict}-")),
        None,
    )


def _parse_record_line(line, where, scope):
    """Parse one JSONL line into a record object, or None with a finding."""
    try:
        item = strict_json_loads(line)
    except (UnicodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        scope.totals["parse_failures"] += 1
        scope.report(where, f"JSON parse error: {exc}")
        return None
    if not isinstance(item, dict):
        scope.totals["parse_failures"] += 1
        scope.report(where, "record is not a JSON object")
        return None
    return item


def _duplicate_id_finding(item, where, seen_ids):
    """Claim this record's id, reporting the coordinate that claimed it first."""
    identifier = item.get("id")
    if not isinstance(identifier, str):
        return None
    if identifier in seen_ids:
        return f"duplicate record id {identifier!r}; first seen at {seen_ids[identifier]}"
    seen_ids[identifier] = where
    return None


def _classify_layers(item, require_runtime, expected_commit=None):
    """Classify one record, containing any internal failure as an envelope finding."""
    try:
        return record.classify(
            item,
            require_named_runtime=require_runtime,
            expected_commit=expected_commit,
        )
    except Exception as exc:  # final boundary around one untrusted record
        return {
            "envelope": [
                f"record validation raised an internal exception: {type(exc).__name__}"
            ],
            "family": [],
            "status": [],
        }


def _fatal_findings(item, layers, identity_finding, scope):
    """The findings that make one record invalid, in emission order."""
    fatal = layers["envelope"] + layers["status"]
    if identity_finding:
        fatal.append(identity_finding)
    family = item.get("family")
    if family != scope.path.parent.name:
        fatal.append(
            f"record family {family!r} does not match directory {scope.path.parent.name!r}"
        )
    declared_verdict = (
        item.get("validation", {}).get("status")
        if isinstance(item.get("validation"), dict)
        else None
    )
    expected_verdict = _verdict_for_file(scope.path.name)
    if expected_verdict and declared_verdict != expected_verdict:
        fatal.append(
            f"record declares verdict {declared_verdict!r} but is filed in "
            f"{scope.path.name!r}, which is reserved for {expected_verdict!r} records"
        )
    return fatal


def _count_valid_record(item, layers, totals):
    """Roll one valid record into the per-run counters."""
    if layers["family"]:
        totals["rejected"] += 1
    else:
        totals["accepted"] += 1
    implementation = item["oracle"]["implementation"]
    if implementation == "reference":
        totals["reference_oracle"] += 1
    elif implementation == "named-runtime":
        totals["named_runtime"] += 1
    else:
        totals["mixed_oracle"] += 1
    if item["validation"].get("publishable"):
        totals["publishable"] += 1


def _reproduce_record(item, where, scope):
    """Re-derive one record's oracle result and count the outcome."""
    try:
        status, detail = record.reproduce(item)
    except Exception as exc:  # defensive boundary around stored data
        status = "invalid"
        detail = f"reproduction raised {type(exc).__name__}"
    scope.totals[f"reproduce_{status}"] += 1
    if status != "reproduced":
        # The record is already tallied as accepted or rejected by
        # _count_valid_record; charging "invalid" as well would make
        # accepted + rejected + invalid exceed records in the report.  The
        # failure still fails the run through the reported finding, and the
        # outcome stays visible in the report's reproduce_* buckets.
        scope.report(where, f"requested oracle reproduction was {status}: {detail}")


def _validate_one_record(item, where, scope):
    """Apply every per-record rule, updating the file's totals and findings."""
    identity_finding = _duplicate_id_finding(item, where, scope.seen_ids)
    if scope.selected and item.get("family") not in scope.selected:
        scope.totals["skipped"] += 1
        if identity_finding:
            scope.totals["invalid"] += 1
            scope.report(where, identity_finding)
        return
    scope.totals["records"] += 1
    layers = _classify_layers(item, scope.require_runtime, scope.expected_commit)
    fatal = _fatal_findings(item, layers, identity_finding, scope)
    if fatal:
        scope.totals["invalid"] += 1
        for finding in fatal:
            scope.report(where, finding)
        return
    _count_valid_record(item, layers, scope.totals)
    if scope.reproduce:
        _reproduce_record(item, where, scope)


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
    expected_verdict = _verdict_for_file(scope.path.name)
    parsed_records = []
    for number, line in enumerate(io.BytesIO(snapshot.body), start=1):
        if not line.strip():
            continue
        where = f"{scope.path}:{number}"
        item = _parse_record_line(line, where, scope)
        if item is None:
            continue
        parsed_records.append(
            ParsedRecord(
                item=item,
                where=where,
                relative=scope.relative,
                verdict=expected_verdict,
            )
        )
        _validate_one_record(item, where, scope)
    return scope.totals, scope.errors, parsed_records


_RUN_FILE_RE = re.compile(
    r"^(?P<family>[^/]+)/(?P<verdict>accepted|rejected)-r"
    r"(?P<round>[0-9]{1,8})\.jsonl$"
)


def _summary(records, manifest_path, label, errors):
    scores = []
    for parsed in records:
        validation = parsed.item.get("validation")
        if not isinstance(validation, dict):
            errors.append(f"{manifest_path}: {label} contains a record without validation")
            continue
        score = validation.get("candidate_prediction_correct")
        if score is not None and not isinstance(score, bool):
            errors.append(f"{manifest_path}: {label} contains a non-boolean candidate score")
            continue
        if score is not None:
            scores.append(score)
    return {
        "records": len(records),
        "candidate_scored": len(scores),
        "candidate_correct": sum(1 for score in scores if score),
    }


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
    """Lift the manifest scalars into one bundle."""
    return _ManifestHeader(
        round_number=manifest.get("round"),
        master_seed=manifest.get("seed"),
        count_per_family=manifest.get("count_per_family"),
        commit=manifest.get("oracle_commit"),
        dirty=manifest.get("oracle_dirty"),
        module_digest=manifest.get("module_digest"),
    )


def _header_field_errors(context):
    """Range- and type-check the manifest scalar fields."""
    header = context.header
    if not header.round_ok:
        context.report(f"round must be an integer in [1, {MAX_ROUND}]")
    if not _plain_int(header.master_seed):
        context.report("seed must be an integer")
    if not header.count_ok:
        context.report(f"count_per_family must be an integer in [1, {MAX_RUN_RECORDS}]")
    if not oracles.is_source_commit(header.commit):
        context.report(
            "oracle_commit must be a resolved lowercase 40- or 64-hex source commit"
        )
    elif oracles.resolve_source_commit(header.commit) != header.commit:
        context.report("oracle_commit does not resolve in the source repository")
    if header.dirty is not None and not isinstance(header.dirty, bool):
        context.report("oracle_dirty must be boolean or null")
    if not canon.is_digest(header.module_digest):
        context.report("module_digest must be a sha256 digest")


def _declared_families_block(manifest, context):
    """Validate the declared families mapping and return it."""
    declared = manifest.get("families")
    if not isinstance(declared, dict):
        context.report("families must be an object")
        return {}
    if not declared:
        context.report("families must declare at least one family")
    elif context.header.count_ok and (
        context.header.count_per_family * len(declared) > MAX_RUN_RECORDS
    ):
        context.report(
            f"count_per_family across declared families exceeds {MAX_RUN_RECORDS} records"
        )
    return declared


def _run_file_layout(snapshots, context):
    """Map each captured file to ``(family, verdict, round)``."""
    header = context.header
    file_info = {}
    actual_families = set()
    for snapshot in snapshots:
        match = _RUN_FILE_RE.fullmatch(snapshot.relative)
        if match is None:
            context.report(f"manifest path is not a canonical run file: {snapshot.relative}")
            continue
        family = match.group("family")
        file_round = int(match.group("round"))
        file_info[snapshot.relative] = (family, match.group("verdict"), file_round)
        actual_families.add(family)
        if family not in families.SPECS:
            context.report(f"run contains unknown family {family!r}")
        if header.round_ok and file_round != header.round_number:
            context.report(
                f"{snapshot.relative} round {file_round} "
                f"does not match manifest round {header.round_number}"
            )
    return file_info, actual_families


def _family_file_pairing_errors(file_info, actual_families, context):
    """Each family must carry exactly one accepted and one rejected file."""
    header = context.header
    if not header.round_ok:
        return
    for family in sorted(actual_families):
        expected_files = {
            f"{family}/accepted-r{header.round_number:02d}.jsonl",
            f"{family}/rejected-r{header.round_number:02d}.jsonl",
        }
        actual_files = {relative for relative, info in file_info.items() if info[0] == family}
        if actual_files != expected_files:
            context.report(
                f"family {family!r} must have exactly one accepted "
                "and one rejected file for the manifest round"
            )


def _record_index(parsed, context):
    """The proposal index encoded in a record id, or None when malformed."""
    identifier = parsed.item.get("id")
    match = (
        re.fullmatch(
            rf"{re.escape(context.family)}-r([0-9]{{1,8}})-([0-9]{{1,10}})",
            identifier,
        )
        if isinstance(identifier, str)
        else None
    )
    if match is None:
        context.report(f"{parsed.where} has no canonical family id")
        return None
    if context.header.round_ok and int(match.group(1)) != context.header.round_number:
        context.report(f"{parsed.where} id round does not match manifest")
    return int(match.group(2))


def _record_oracle_binding_errors(parsed, oracle, index, context):
    """Bind one record's oracle block to the manifest, returning its implementation."""
    header = context.header
    implementation = oracle.get("implementation")
    if not isinstance(implementation, str):
        context.report(f"{parsed.where} oracle.implementation must be a string")
        implementation = None
    if oracle.get("commit") != header.commit:
        context.report(f"{parsed.where} oracle.commit disagrees")
    if oracle.get("dirty") is not header.dirty:
        context.report(f"{parsed.where} oracle.dirty disagrees")
    if oracle.get("module_digest") != header.module_digest:
        context.report(f"{parsed.where} oracle.module_digest disagrees")
    if _plain_int(header.master_seed) and index is not None:
        _record_seed_errors(parsed, oracle, index, context)
    meta = parsed.item.get("meta")
    if not isinstance(meta, dict) or meta.get("round") != header.round_number:
        context.report(f"{parsed.where} meta.round disagrees")
    return implementation


def _record_seed_errors(parsed, oracle, index, context):
    """Both the oracle and generator seeds must derive from the manifest seed."""
    expected_seed = seed_from_label(context.header.master_seed, f"{context.family}:{index}")
    if oracle.get("seed") != expected_seed:
        context.report(f"{parsed.where} oracle.seed does not derive from the manifest seed")
    generator = parsed.item.get("generator")
    if not isinstance(generator, dict) or generator.get("seed") != expected_seed:
        context.report(f"{parsed.where} generator.seed does not derive from the manifest seed")


def _record_availability_errors(parsed, oracle, context):
    """Runtime availability probes must stay identical across the run."""
    availability = oracle.get("availability")
    if not isinstance(availability, dict):
        # The record envelope already rejects this shape; report rather than
        # skip so this cross-check never silently passes a malformed block.
        context.report(f"{parsed.where} has malformed runtime availability")
        return
    record_probes = availability.get("runtimes")
    if not isinstance(record_probes, list):
        context.report(f"{parsed.where} has malformed runtime availability")
        record_probes = []
    for probe in record_probes:
        if not (isinstance(probe, dict) and isinstance(probe.get("runtime"), str)):
            context.report(f"{parsed.where} has malformed runtime availability")
            continue
        try:
            normalized = canon.normalize(probe)
        except (TypeError, ValueError, RecursionError) as exc:
            context.report(
                f"{parsed.where} has malformed runtime availability: {type(exc).__name__}"
            )
            continue
        previous = context.probe_values.setdefault(probe["runtime"], normalized)
        if previous != normalized:
            context.report("runtime availability changes within the run")


def _collect_rejection_reasons(parsed, reasons, context):
    """Accumulate the declared rejection reasons for one rejected record."""
    validation = parsed.item.get("validation")
    declared = validation.get("reasons") if isinstance(validation, dict) else None
    if not isinstance(declared, list) or not all(
        isinstance(reason, str) for reason in declared
    ):
        context.report(f"{parsed.where} has malformed rejection reasons")
        return
    reasons.update(declared)


def _indexes_are_complete(indexes, context):
    """Whether the captured ids cover each proposal index exactly once."""
    if not context.header.count_ok:
        return False
    return len(indexes) == context.header.count_per_family and all(
        index == expected for expected, index in enumerate(sorted(indexes))
    )


def _family_summary(family, records, context):
    """Validate one family's records and rebuild the summary it must declare."""
    header = context.header
    if header.count_ok and len(records) != header.count_per_family:
        context.report(
            f"family {family!r} has {len(records)} captured records, "
            f"expected {header.count_per_family}"
        )
    indexes = []
    implementations = []
    accepted = [parsed for parsed in records if parsed.verdict == "accepted"]
    rejected = [parsed for parsed in records if parsed.verdict == "rejected"]
    rejection_reasons = set()
    for parsed in records:
        index = _record_index(parsed, context)
        if index is not None:
            indexes.append(index)
        oracle = parsed.item.get("oracle")
        if not isinstance(oracle, dict):
            context.report(f"{parsed.where} has no oracle object")
            continue
        implementation = _record_oracle_binding_errors(parsed, oracle, index, context)
        if implementation is not None:
            implementations.append(implementation)
        _record_availability_errors(parsed, oracle, context)
        if parsed.verdict == "rejected":
            _collect_rejection_reasons(parsed, rejection_reasons, context)
    if header.count_ok and not _indexes_are_complete(indexes, context):
        context.report(f"family {family!r} ids do not cover each proposal index once")
    if len(set(implementations)) > 1:
        context.report(f"family {family!r} mixes oracle implementations")
    spec = families.SPECS.get(family)
    return {
        "proposed": header.count_per_family,
        "accepted": _summary(
            accepted, context.manifest_path, f"families[{family!r}].accepted", context.errors
        ),
        "rejected": {
            "records": len(rejected),
            "reasons": sorted(rejection_reasons),
        },
        "oracle": {
            "requested_runtime": list(spec.runtimes) if spec is not None else [],
            "implementation": implementations[0] if implementations else None,
        },
    }


def _group_records_by_family(parsed_records, file_info, actual_families):
    """Bucket parsed records under the family directory that carried them."""
    by_family = {family: [] for family in actual_families}
    for parsed in parsed_records:
        info = file_info.get(parsed.relative)
        if info is not None:
            by_family.setdefault(info[0], []).append(parsed)
    return by_family


def _expected_runtime_set(actual_families):
    """Every runtime the captured families request."""
    return {
        runtime
        for family in actual_families
        if family in families.SPECS
        for runtime in families.spec_for(family).runtimes
    }


def _availability_probe_errors(probes, context):
    """Each declared probe must match the one captured in the records."""
    for probe in probes:
        if not isinstance(probe, dict) or not isinstance(probe.get("runtime"), str):
            # The sibling runtime-name check already rejects these shapes;
            # report rather than skip so a malformed probe can never pass.
            context.report("availability declares a malformed runtime probe")
            continue
        runtime = probe["runtime"]
        expected_probe = context.probe_values.get(runtime)
        if (
            expected_probe is None
            or probe != expected_probe
            or probe.get("binding_env") != oracles.env_key(runtime)
            or not isinstance(probe.get("bound"), bool)
        ):
            context.report(
                f"availability for runtime {runtime!r} does not match captured records"
            )


def _availability_rollup_errors(availability, probes, runtime_names, context):
    """``all_bound`` and ``unbound`` must follow from the declared probes."""
    # A set keeps this linear: probe counts are untrusted and bounded only by
    # the manifest byte limit. Non-string runtimes can never match a string
    # name, so excluding them from the set changes no outcome.
    bound = {
        probe.get("runtime")
        for probe in probes
        if isinstance(probe, dict)
        and probe.get("bound") is True
        and isinstance(probe.get("runtime"), str)
    }
    unbound = (
        [runtime for runtime in runtime_names if runtime not in bound]
        if all(isinstance(runtime, str) for runtime in runtime_names)
        else []
    )
    if availability.get("all_bound") is not (not unbound):
        context.report("oracle_availability.all_bound disagrees")
    if availability.get("unbound") != unbound:
        context.report("oracle_availability.unbound disagrees")


def _availability_block_errors(manifest, actual_families, context):
    """Validate the manifest's oracle_availability block."""
    availability = manifest.get("oracle_availability")
    if not isinstance(availability, dict):
        context.report("oracle_availability must be an object")
        return
    # Exactly the fields availability_report() emits; an undeclared sibling
    # would be an unsupported provenance claim in canonical run metadata.
    unknown = sorted(set(availability) - {"protocol", "runtimes", "all_bound", "unbound"})
    if unknown:
        context.report(
            "oracle_availability carries unauthenticated sibling keys: " + ", ".join(unknown)
        )
    probes = availability.get("runtimes")
    if availability.get("protocol") != oracles.PROTOCOL or not isinstance(probes, list):
        context.report("oracle_availability is malformed")
        return
    runtime_names = [
        probe.get("runtime") if isinstance(probe, dict) else None for probe in probes
    ]
    runtime_names_valid = all(isinstance(runtime, str) for runtime in runtime_names)
    if not runtime_names_valid:
        context.report("oracle_availability runtime names must be strings")
    elif (
        len(runtime_names) != len(set(runtime_names))
        or set(runtime_names) != _expected_runtime_set(actual_families)
    ):
        context.report("oracle_availability runtimes do not match families")
    _availability_probe_errors(probes, context)
    _availability_rollup_errors(availability, probes, runtime_names, context)


def _manifest_metadata_errors(manifest, snapshots, parsed_records, run_dir):
    """Bind manifest metadata and summaries to the captured record snapshot."""
    context = _MetadataContext(
        header=_read_manifest_header(manifest),
        manifest_path=Path(run_dir) / "manifest.json",
        errors=[],
        probe_values={},
    )
    # The manifest is canonical run metadata that no other digest covers, so
    # its vocabulary is closed: an undeclared sibling would be an unsupported
    # provenance claim riding along with an otherwise valid run.
    unknown = sorted(set(manifest) - MANIFEST_ALLOWED_KEYS)
    if unknown:
        context.report("manifest carries unauthenticated sibling keys: " + ", ".join(unknown))
    _header_field_errors(context)
    declared_families = _declared_families_block(manifest, context)

    file_info, actual_families = _run_file_layout(snapshots, context)
    if set(declared_families) != actual_families:
        context.report("families keys do not match captured family directories")
    _family_file_pairing_errors(file_info, actual_families, context)

    by_family = _group_records_by_family(parsed_records, file_info, actual_families)
    expected_summaries = {
        family: _family_summary(family, by_family.get(family, []), context.bound(family))
        for family in sorted(actual_families)
    }
    if declared_families != expected_summaries:
        context.report(
            "per-family counts, reasons, scores, or oracle summaries "
            "do not match the captured records"
        )
    if context.header.module_digest != oracles.module_digest():
        context.report("module_digest does not match the current reference implementation")

    _availability_block_errors(manifest, actual_families, context)
    _manifest_note_errors(manifest, parsed_records, context)
    return context.errors


def _manifest_note_errors(manifest, parsed_records, context):
    """The note is derived provenance, not free text: recompute it.

    ``build_manifest`` chooses between exactly two notes based on whether any
    captured record is publishable.  An unvalidated note could otherwise claim
    external attestation or publishability that no record carries.
    """
    any_publishable = any(
        isinstance(parsed.item.get("validation"), dict)
        and parsed.item["validation"].get("publishable") is True
        for parsed in parsed_records
    )
    expected = MANIFEST_NOTE_PUBLISHABLE if any_publishable else MANIFEST_NOTE_UNPUBLISHABLE
    if manifest.get("note") != expected:
        context.report("note does not match the publishability of the captured records")


def validate_run(run_dir, require_runtime=False, reproduce=False, selected=()):
    totals = Counter()
    errors = []
    by_family = Counter()
    manifest, snapshots, manifest_errors = authenticate_manifest(run_dir)
    errors.extend(manifest_errors)
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
    seen_ids = {}
    parsed_records = []
    for snapshot in snapshots:
        file_totals, file_errors, file_records = validate_file(
            snapshot,
            require_runtime,
            reproduce,
            selected,
            seen_ids=seen_ids,
            expected_commit=expected_commit,
        )
        totals.update(file_totals)
        errors.extend(file_errors)
        parsed_records.extend(file_records)
        if file_totals["records"]:
            # Skip zero entries so a --family filter reports only what it kept.
            by_family[snapshot.path.parent.name] += file_totals["records"]
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
    if reproduce:
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

    report, errors = validate_run(
        run_dir,
        require_runtime=args.require_runtime,
        reproduce=args.reproduce,
        selected=selected,
    )
    print(json.dumps(report, indent=2))
    finding_limit = max(0, args.max_findings)
    for finding in errors[:finding_limit]:
        print(finding, file=sys.stderr)
    hidden = max(0, len(errors) - finding_limit)
    if hidden:
        print(f"... {hidden} more findings", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
