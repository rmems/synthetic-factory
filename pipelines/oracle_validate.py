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
import os
import re
import stat
import sys
from collections import Counter
from dataclasses import dataclass
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


def strict_json_loads(text):
    value = json.loads(
        text,
        object_pairs_hook=_object_from_pairs,
        parse_constant=_reject_constant,
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


def _snapshot_regular_file(root_fd, path, relative, limit, expected_stat):
    """Capture one root-relative path once and detect identity or byte changes."""
    path = Path(path)
    if expected_stat.st_size > limit:
        raise ValueError(f"file exceeds the {limit}-byte snapshot limit")
    descriptor = _open_beneath(root_fd, relative)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise ValueError("opened object is not a singly linked regular file")
        expected_identity = (
            expected_stat.st_dev,
            expected_stat.st_ino,
            expected_stat.st_mode,
            expected_stat.st_size,
            expected_stat.st_mtime_ns,
            expected_stat.st_ctime_ns,
            expected_stat.st_nlink,
        )
        opened_identity = (
            before.st_dev,
            before.st_ino,
            before.st_mode,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
            before.st_nlink,
        )
        if opened_identity != expected_identity:
            raise ValueError("file changed after run-tree enumeration")
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
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    identity_before = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
        before.st_nlink,
    )
    identity_after = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
        after.st_nlink,
    )
    if identity_before != identity_after:
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


def _enumerate_run_files(run_dir, root_fd):
    """List one opened run tree without following directory links."""
    root = Path(run_dir)
    errors = []
    files = {}
    stack = [(PurePosixPath(), os.dup(root_fd))]
    entries_seen = 0
    bytes_seen = 0
    try:
        while stack:
            prefix, directory_fd = stack.pop()
            directory = root / prefix
            try:
                with os.scandir(directory_fd) as iterator:
                    entries = sorted(iterator, key=lambda entry: entry.name)
                for entry in entries:
                    entries_seen += 1
                    if entries_seen > MAX_RUN_ENTRIES:
                        errors.append(f"{root}: run contains more than {MAX_RUN_ENTRIES} entries")
                        return files, errors
                    relative_path = prefix / entry.name
                    relative = relative_path.as_posix()
                    try:
                        entry_stat = entry.stat(follow_symlinks=False)
                    except OSError as exc:
                        errors.append(
                            f"{root / relative}: could not inspect entry: {type(exc).__name__}"
                        )
                        continue
                    if stat.S_ISLNK(entry_stat.st_mode):
                        errors.append(f"{root / relative}: symbolic links are not allowed in a run")
                    elif stat.S_ISDIR(entry_stat.st_mode):
                        if len(relative_path.parts) > MAX_RUN_DEPTH:
                            errors.append(
                                f"{root / relative}: run nesting exceeds "
                                f"{MAX_RUN_DEPTH} directories"
                            )
                            continue
                        flags = (
                            os.O_RDONLY
                            | getattr(os, "O_CLOEXEC", 0)
                            | getattr(os, "O_DIRECTORY", 0)
                            | getattr(os, "O_NOFOLLOW", 0)
                        )
                        try:
                            child_fd = os.open(entry.name, flags, dir_fd=directory_fd)
                            child_stat = os.fstat(child_fd)
                        except OSError as exc:
                            errors.append(
                                f"{root / relative}: could not open directory safely: "
                                f"{type(exc).__name__}"
                            )
                            continue
                        if (child_stat.st_dev, child_stat.st_ino) != (
                            entry_stat.st_dev,
                            entry_stat.st_ino,
                        ):
                            os.close(child_fd)
                            errors.append(
                                f"{root / relative}: directory changed during enumeration"
                            )
                            continue
                        stack.append((relative_path, child_fd))
                    elif stat.S_ISREG(entry_stat.st_mode):
                        if entry_stat.st_nlink != 1:
                            errors.append(
                                f"{root / relative}: hard-linked files are not allowed in a run"
                            )
                        files[relative] = (root / relative, entry_stat)
                        bytes_seen += entry_stat.st_size
                        if bytes_seen > MAX_RUN_BYTES:
                            errors.append(
                                f"{root}: run exceeds the {MAX_RUN_BYTES}-byte snapshot limit"
                            )
                            return files, errors
                        if len(files) > MAX_RUN_FILES:
                            errors.append(f"{root}: run contains more than {MAX_RUN_FILES} files")
                            return files, errors
                    else:
                        errors.append(
                            f"{root / relative}: only regular files and directories are allowed"
                        )
            except OSError as exc:
                errors.append(f"{directory}: could not enumerate directory: {type(exc).__name__}")
            finally:
                os.close(directory_fd)
    finally:
        for _prefix, descriptor in stack:
            os.close(descriptor)
    return files, errors


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


def _authenticate_manifest_from_root(run_dir, root_fd):
    """Authenticate a run rooted at one already pinned directory descriptor."""
    run_dir = Path(run_dir)
    errors = []
    actual, tree_errors = _enumerate_run_files(run_dir, root_fd)
    errors.extend(tree_errors)
    manifest_path = run_dir / "manifest.json"
    manifest = None
    manifest_entry = actual.get("manifest.json")
    if manifest_entry is None:
        errors.append(f"{manifest_path}: required run manifest is missing")
    else:
        try:
            manifest_file, manifest_stat = manifest_entry
            manifest_snapshot = _snapshot_regular_file(
                root_fd,
                manifest_file,
                "manifest.json",
                MAX_MANIFEST_BYTES,
                expected_stat=manifest_stat,
            )
            manifest = strict_json_loads(manifest_snapshot.body)
        except (
            OSError,
            UnicodeError,
            json.JSONDecodeError,
            ValueError,
            RecursionError,
            MemoryError,
        ) as exc:
            errors.append(
                f"{manifest_path}: invalid manifest snapshot: {type(exc).__name__}: {exc}"
            )
            manifest = None

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

    expected_names = set()
    valid_entries = {}
    declared_record_total = 0
    for relative, entry in entries.items():
        safe_path = _safe_manifest_path(relative)
        if safe_path is None:
            errors.append(f"{manifest_path}: unsafe manifest file path {relative!r}")
            continue
        expected_names.add(relative)
        if not isinstance(entry, dict):
            errors.append(f"{manifest_path}: files[{relative!r}] must be an object")
            continue
        digest = entry.get("sha256")
        count = entry.get("records")
        if not (
            isinstance(digest, str)
            and len(digest) == 64
            and all(character in "0123456789abcdef" for character in digest)
        ):
            errors.append(f"{manifest_path}: files[{relative!r}].sha256 is invalid")
            continue
        if not _plain_int(count, minimum=0, maximum=MAX_RUN_RECORDS):
            errors.append(f"{manifest_path}: files[{relative!r}].records is invalid")
            continue
        declared_record_total += count
        if declared_record_total > MAX_RUN_RECORDS:
            errors.append(f"{manifest_path}: declared record total exceeds {MAX_RUN_RECORDS}")
            continue
        valid_entries[relative] = entry
    if declared_record_total == 0:
        errors.append(f"{manifest_path}: declared run contains no records")

    for relative in sorted(expected_names - actual_names):
        errors.append(f"{manifest_path}: manifest file is missing: {relative}")
    for relative in sorted(actual_names - expected_names):
        errors.append(f"{manifest_path}: unmanifested file is present: {relative}")

    snapshots = []
    seen_inodes = set()
    captured_record_total = 0
    for relative in sorted(expected_names & actual_names & valid_entries.keys()):
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
        actual_digest = hashlib.sha256(snapshot.body).hexdigest()
        expected_digest = valid_entries[relative]["sha256"]
        if actual_digest != expected_digest:
            errors.append(
                f"{path}: sha256 mismatch: manifest {expected_digest}, actual {actual_digest}"
            )
        actual_count = sum(1 for line in io.BytesIO(snapshot.body) if line.strip())
        expected_count = valid_entries[relative]["records"]
        if actual_count != expected_count:
            errors.append(
                f"{path}: record-count mismatch: manifest {expected_count}, actual {actual_count}"
            )
        captured_record_total += actual_count
        if captured_record_total > MAX_RUN_RECORDS:
            errors.append(f"{path}: captured record total exceeds {MAX_RUN_RECORDS}")
            continue
        snapshots.append(snapshot)
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


def validate_file(snapshot, require_runtime, reproduce, selected, seen_ids=None):
    """Validate one captured JSONL snapshot. Returns totals, errors, records."""
    totals = Counter()
    errors = []
    parsed_records = []
    seen_ids = {} if seen_ids is None else seen_ids
    path = snapshot.path
    for number, line in enumerate(io.BytesIO(snapshot.body), start=1):
        if not line.strip():
            continue
        where = f"{path}:{number}"
        try:
            item = strict_json_loads(line)
        except (UnicodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
            totals["parse_failures"] += 1
            errors.append(f"{where}: JSON parse error: {exc}")
            continue
        if not isinstance(item, dict):
            totals["parse_failures"] += 1
            errors.append(f"{where}: record is not a JSON object")
            continue
        family = item.get("family")
        expected_verdict = next(
            (
                verdict
                for verdict in ("accepted", "rejected")
                if path.name.startswith(f"{verdict}-")
            ),
            None,
        )
        parsed_records.append(
            ParsedRecord(
                item=item,
                where=where,
                relative=snapshot.relative,
                verdict=expected_verdict,
            )
        )
        identity_finding = None
        identifier = item.get("id")
        if isinstance(identifier, str):
            if identifier in seen_ids:
                identity_finding = (
                    f"duplicate record id {identifier!r}; first seen at {seen_ids[identifier]}"
                )
            else:
                seen_ids[identifier] = where
        if selected and family not in selected:
            totals["skipped"] += 1
            if identity_finding:
                totals["invalid"] += 1
                errors.append(f"{where}: {identity_finding}")
            continue
        totals["records"] += 1

        try:
            layers = record.classify(item, require_named_runtime=require_runtime)
        except Exception as exc:  # final boundary around one untrusted record
            layers = {
                "envelope": [
                    f"record validation raised an internal exception: {type(exc).__name__}"
                ],
                "family": [],
                "status": [],
            }
        fatal = layers["envelope"] + layers["status"]
        if identity_finding:
            fatal.append(identity_finding)
        if family != path.parent.name:
            fatal.append(f"record family {family!r} does not match directory {path.parent.name!r}")
        declared_verdict = (
            item.get("validation", {}).get("status")
            if isinstance(item.get("validation"), dict)
            else None
        )
        if expected_verdict and declared_verdict != expected_verdict:
            fatal.append(
                f"record declares verdict {declared_verdict!r} but is filed in "
                f"{path.name!r}, which is reserved for {expected_verdict!r} records"
            )
        if fatal:
            totals["invalid"] += 1
            for finding in fatal:
                errors.append(f"{where}: {finding}")
            continue
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

        if reproduce:
            try:
                status, detail = record.reproduce(item)
            except Exception as exc:  # defensive boundary around stored data
                status = "invalid"
                detail = f"reproduction raised {type(exc).__name__}"
            totals[f"reproduce_{status}"] += 1
            if status != "reproduced":
                totals["invalid"] += 1
                errors.append(f"{where}: requested oracle reproduction was {status}: {detail}")
    return totals, errors, parsed_records


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


def _manifest_metadata_errors(manifest, snapshots, parsed_records, run_dir):
    """Bind manifest metadata and summaries to the captured record snapshot."""
    manifest_path = Path(run_dir) / "manifest.json"
    errors = []
    round_number = manifest.get("round")
    master_seed = manifest.get("seed")
    count_per_family = manifest.get("count_per_family")
    if not _plain_int(round_number, minimum=1, maximum=MAX_ROUND):
        errors.append(f"{manifest_path}: round must be an integer in [1, {MAX_ROUND}]")
    if not _plain_int(master_seed):
        errors.append(f"{manifest_path}: seed must be an integer")
    if not _plain_int(count_per_family, minimum=1, maximum=MAX_RUN_RECORDS):
        errors.append(
            f"{manifest_path}: count_per_family must be an integer in [1, {MAX_RUN_RECORDS}]"
        )
    commit = manifest.get("oracle_commit")
    if not oracles.is_source_commit(commit):
        errors.append(
            f"{manifest_path}: oracle_commit must be a resolved lowercase "
            "40- or 64-hex source commit"
        )
    elif oracles.resolve_source_commit(commit) != commit:
        errors.append(f"{manifest_path}: oracle_commit does not resolve in the source repository")
    dirty = manifest.get("oracle_dirty")
    if dirty is not None and not isinstance(dirty, bool):
        errors.append(f"{manifest_path}: oracle_dirty must be boolean or null")
    module_digest = manifest.get("module_digest")
    if not canon.is_digest(module_digest):
        errors.append(f"{manifest_path}: module_digest must be a sha256 digest")
    declared_families = manifest.get("families")
    if not isinstance(declared_families, dict):
        errors.append(f"{manifest_path}: families must be an object")
        declared_families = {}
    elif not declared_families:
        errors.append(f"{manifest_path}: families must declare at least one family")
    elif _plain_int(count_per_family, minimum=1, maximum=MAX_RUN_RECORDS) and (
        count_per_family * len(declared_families) > MAX_RUN_RECORDS
    ):
        errors.append(
            f"{manifest_path}: count_per_family across declared families exceeds "
            f"{MAX_RUN_RECORDS} records"
        )

    file_info = {}
    actual_families = set()
    for snapshot in snapshots:
        match = _RUN_FILE_RE.fullmatch(snapshot.relative)
        if match is None:
            errors.append(
                f"{manifest_path}: manifest path is not a canonical run file: {snapshot.relative}"
            )
            continue
        family = match.group("family")
        verdict = match.group("verdict")
        file_round = int(match.group("round"))
        file_info[snapshot.relative] = (family, verdict, file_round)
        actual_families.add(family)
        if family not in families.SPECS:
            errors.append(f"{manifest_path}: run contains unknown family {family!r}")
        if _plain_int(round_number, minimum=1, maximum=MAX_ROUND) and file_round != round_number:
            errors.append(
                f"{manifest_path}: {snapshot.relative} round {file_round} "
                f"does not match manifest round {round_number}"
            )
    if set(declared_families) != actual_families:
        errors.append(f"{manifest_path}: families keys do not match captured family directories")
    for family in sorted(actual_families):
        expected_files = {
            f"{family}/accepted-r{round_number:02d}.jsonl"
            if _plain_int(round_number, minimum=1, maximum=MAX_ROUND)
            else None,
            f"{family}/rejected-r{round_number:02d}.jsonl"
            if _plain_int(round_number, minimum=1, maximum=MAX_ROUND)
            else None,
        }
        actual_files = {relative for relative, info in file_info.items() if info[0] == family}
        if None not in expected_files and actual_files != expected_files:
            errors.append(
                f"{manifest_path}: family {family!r} must have exactly one accepted "
                "and one rejected file for the manifest round"
            )

    by_family = {family: [] for family in actual_families}
    for parsed in parsed_records:
        info = file_info.get(parsed.relative)
        if info is not None:
            by_family.setdefault(info[0], []).append(parsed)

    reference_seen = False
    probe_values = {}
    expected_summaries = {}
    for family in sorted(actual_families):
        records = by_family.get(family, [])
        if (
            _plain_int(count_per_family, minimum=1, maximum=MAX_RUN_RECORDS)
            and len(records) != count_per_family
        ):
            errors.append(
                f"{manifest_path}: family {family!r} has {len(records)} captured records, "
                f"expected {count_per_family}"
            )
        indexes = []
        implementations = []
        accepted = [parsed for parsed in records if parsed.verdict == "accepted"]
        rejected = [parsed for parsed in records if parsed.verdict == "rejected"]
        rejection_reasons = set()
        for parsed in records:
            item = parsed.item
            identifier = item.get("id")
            identifier_match = (
                re.fullmatch(
                    rf"{re.escape(family)}-r([0-9]{{1,8}})-([0-9]{{1,10}})",
                    identifier,
                )
                if isinstance(identifier, str)
                else None
            )
            if identifier_match is None:
                errors.append(f"{manifest_path}: {parsed.where} has no canonical family id")
                index = None
            else:
                item_round = int(identifier_match.group(1))
                index = int(identifier_match.group(2))
                indexes.append(index)
                if (
                    _plain_int(round_number, minimum=1, maximum=MAX_ROUND)
                    and item_round != round_number
                ):
                    errors.append(
                        f"{manifest_path}: {parsed.where} id round does not match manifest"
                    )
            oracle = item.get("oracle")
            generator = item.get("generator")
            meta = item.get("meta")
            if not isinstance(oracle, dict):
                errors.append(f"{manifest_path}: {parsed.where} has no oracle object")
                continue
            implementation = oracle.get("implementation")
            if not isinstance(implementation, str):
                errors.append(
                    f"{manifest_path}: {parsed.where} oracle.implementation must be a string"
                )
            else:
                implementations.append(implementation)
                if implementation in ("reference", "mixed"):
                    reference_seen = True
            stages = oracle.get("stages")
            if isinstance(stages, list) and any(
                isinstance(stage, dict) and stage.get("implementation") == "reference"
                for stage in stages
            ):
                reference_seen = True
            if oracle.get("commit") != commit:
                errors.append(f"{manifest_path}: {parsed.where} oracle.commit disagrees")
            if oracle.get("dirty") is not dirty:
                errors.append(f"{manifest_path}: {parsed.where} oracle.dirty disagrees")
            if oracle.get("module_digest") != module_digest:
                errors.append(f"{manifest_path}: {parsed.where} oracle.module_digest disagrees")
            if _plain_int(master_seed) and index is not None:
                expected_seed = seed_from_label(master_seed, f"{family}:{index}")
                if oracle.get("seed") != expected_seed:
                    errors.append(
                        f"{manifest_path}: {parsed.where} oracle.seed does not derive "
                        "from the manifest seed"
                    )
                if not isinstance(generator, dict) or generator.get("seed") != expected_seed:
                    errors.append(
                        f"{manifest_path}: {parsed.where} generator.seed does not derive "
                        "from the manifest seed"
                    )
            if not isinstance(meta, dict) or meta.get("round") != round_number:
                errors.append(f"{manifest_path}: {parsed.where} meta.round disagrees")
            availability = oracle.get("availability")
            if isinstance(availability, dict):
                record_probes = availability.get("runtimes")
                if not isinstance(record_probes, list):
                    errors.append(
                        f"{manifest_path}: {parsed.where} has malformed runtime availability"
                    )
                    record_probes = []
                for probe in record_probes:
                    if isinstance(probe, dict) and isinstance(probe.get("runtime"), str):
                        try:
                            normalized = canon.normalize(probe)
                        except (TypeError, ValueError, RecursionError) as exc:
                            errors.append(
                                f"{manifest_path}: {parsed.where} has malformed runtime "
                                f"availability: {type(exc).__name__}"
                            )
                            continue
                        previous = probe_values.setdefault(probe["runtime"], normalized)
                        if previous != normalized:
                            errors.append(
                                f"{manifest_path}: runtime availability changes within the run"
                            )
            if parsed.verdict == "rejected":
                validation = item.get("validation")
                reasons = validation.get("reasons") if isinstance(validation, dict) else None
                if not isinstance(reasons, list) or not all(
                    isinstance(reason, str) for reason in reasons
                ):
                    errors.append(
                        f"{manifest_path}: {parsed.where} has malformed rejection reasons"
                    )
                else:
                    rejection_reasons.update(reasons)
        indexes_are_complete = (
            len(indexes) == count_per_family
            and all(index == expected for expected, index in enumerate(sorted(indexes)))
            if _plain_int(count_per_family, minimum=1, maximum=MAX_RUN_RECORDS)
            else False
        )
        if (
            _plain_int(count_per_family, minimum=1, maximum=MAX_RUN_RECORDS)
            and not indexes_are_complete
        ):
            errors.append(
                f"{manifest_path}: family {family!r} ids do not cover each proposal index once"
            )
        if len(set(implementations)) > 1:
            errors.append(f"{manifest_path}: family {family!r} mixes oracle implementations")
        implementation = implementations[0] if implementations else None
        spec = families.SPECS.get(family)
        expected_summaries[family] = {
            "proposed": count_per_family,
            "accepted": _summary(accepted, manifest_path, f"families[{family!r}].accepted", errors),
            "rejected": {
                "records": len(rejected),
                "reasons": sorted(rejection_reasons),
            },
            "oracle": {
                "requested_runtime": list(spec.runtimes) if spec is not None else [],
                "implementation": implementation,
            },
        }
    if declared_families != expected_summaries:
        errors.append(
            f"{manifest_path}: per-family counts, reasons, scores, or oracle summaries "
            "do not match the captured records"
        )
    if reference_seen and module_digest != oracles.module_digest():
        errors.append(
            f"{manifest_path}: module_digest does not match the current reference implementation"
        )

    availability = manifest.get("oracle_availability")
    if not isinstance(availability, dict):
        errors.append(f"{manifest_path}: oracle_availability must be an object")
    else:
        probes = availability.get("runtimes")
        if availability.get("protocol") != oracles.PROTOCOL or not isinstance(probes, list):
            errors.append(f"{manifest_path}: oracle_availability is malformed")
        else:
            expected_runtime_set = {
                runtime
                for family in actual_families
                if family in families.SPECS
                for runtime in families.spec_for(family).runtimes
            }
            runtime_names = [
                probe.get("runtime") if isinstance(probe, dict) else None for probe in probes
            ]
            runtime_names_valid = all(isinstance(runtime, str) for runtime in runtime_names)
            if not runtime_names_valid:
                errors.append(f"{manifest_path}: oracle_availability runtime names must be strings")
            elif (
                len(runtime_names) != len(set(runtime_names))
                or set(runtime_names) != expected_runtime_set
            ):
                errors.append(
                    f"{manifest_path}: oracle_availability runtimes do not match families"
                )
            for probe in probes:
                if not isinstance(probe, dict):
                    continue
                runtime = probe.get("runtime")
                if not isinstance(runtime, str):
                    continue
                expected_probe = probe_values.get(runtime)
                if (
                    expected_probe is None
                    or probe != expected_probe
                    or probe.get("binding_env") != oracles.env_key(runtime)
                    or not isinstance(probe.get("bound"), bool)
                ):
                    errors.append(
                        f"{manifest_path}: availability for runtime {runtime!r} "
                        "does not match captured records"
                    )
            bound = [
                probe.get("runtime")
                for probe in probes
                if isinstance(probe, dict) and probe.get("bound") is True
            ]
            unbound = (
                [runtime for runtime in runtime_names if runtime not in bound]
                if runtime_names_valid
                else []
            )
            if availability.get("all_bound") is not (not unbound):
                errors.append(f"{manifest_path}: oracle_availability.all_bound disagrees")
            if availability.get("unbound") != unbound:
                errors.append(f"{manifest_path}: oracle_availability.unbound disagrees")
    return errors


def validate_run(run_dir, require_runtime=False, reproduce=False, selected=()):
    totals = Counter()
    errors = []
    by_family = Counter()
    manifest, snapshots, manifest_errors = authenticate_manifest(run_dir)
    errors.extend(manifest_errors)
    seen_ids = {}
    parsed_records = []
    for snapshot in snapshots:
        file_totals, file_errors, file_records = validate_file(
            snapshot,
            require_runtime,
            reproduce,
            selected,
            seen_ids=seen_ids,
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
