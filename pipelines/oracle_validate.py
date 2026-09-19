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

import argparse as _argparse
import hashlib as _hashlib
import io as _io
import json
import math
import os as _os
import re
import stat as _stat
import sys
from collections import Counter as _Counter
from dataclasses import dataclass, field, replace
from pathlib import Path, PurePosixPath as _PurePosixPath

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("oracle_validate")
    from . import oracle_validate_records as _oracle_validate_records
    from . import oracle_validate_tree as _oracle_validate_tree
    from . import oracle_validate_snapshot as _oracle_validate_snapshot
    from . import oracle_validate_capture as _oracle_validate_capture
    from . import oracle_validate_run as _oracle_validate_run
    from . import oracle_validate_manifest as _oracle_validate_manifest
    from . import oracle_validate_manifest_records as _oracle_validate_manifest_records
    from .oracle_grounded import (
        canon as _canon,
        families as _families,
        oracles as _oracles,
        record as _record,
    )
    from .oracle_grounded import rng as _rng
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_validate"
    )
    import oracle_validate_records as _oracle_validate_records
    import oracle_validate_tree as _oracle_validate_tree
    import oracle_validate_snapshot as _oracle_validate_snapshot
    import oracle_validate_capture as _oracle_validate_capture
    import oracle_validate_run as _oracle_validate_run
    import oracle_validate_manifest as _oracle_validate_manifest
    import oracle_validate_manifest_records as _oracle_validate_manifest_records
    from oracle_grounded import (
        canon as _canon,
        families as _families,
        oracles as _oracles,
        record as _record,
    )
    from oracle_grounded import rng as _rng

# Re-exported for the delegated check classes, which read these through
# ``self.api`` -- the live module namespace of this facade.
canon = _canon
families = _families
oracles = _oracles
record = _record
argparse = _argparse
hashlib = _hashlib
io = _io
os = _os
stat = _stat
Counter = _Counter
PurePosixPath = _PurePosixPath
MAX_SEED = _rng.MAX_SEED
seed_from_label = _rng.seed_from_label

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


def _plain_int(value, *, minimum=None, maximum=None):
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and (minimum is None or value >= minimum)
        and (maximum is None or value <= maximum)
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


_RUN_FILE_RE = re.compile(
    r"^(?P<family>[^/]+)/(?P<verdict>accepted|rejected)-r"
    r"(?P<round>[0-9]{1,8})\.jsonl$"
)


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


@dataclass(frozen=True)
class ValidationContext:
    """The validation request shared by every file of one run."""

    run_dir: object = None
    require_runtime: bool = False
    reproduce: bool = False
    selected: tuple = ()
    oracle_rust_bin: object = None


_TREE_CHECKS = _oracle_validate_tree.RunTreeChecks(sys.modules[__name__])
_record_regular_file = _TREE_CHECKS._record_regular_file
_push_subdirectory = _TREE_CHECKS._push_subdirectory
_scan_entry = _TREE_CHECKS._scan_entry
_scan_directory = _TREE_CHECKS._scan_directory
_enumerate_run_files = _TREE_CHECKS._enumerate_run_files

_RECORD_CHECKS = _oracle_validate_records.RecordChecks(sys.modules[__name__])
_verdict_for_file = _RECORD_CHECKS._verdict_for_file
_parse_record_line = _RECORD_CHECKS._parse_record_line
_duplicate_id_finding = _RECORD_CHECKS._duplicate_id_finding
_classify_layers = _RECORD_CHECKS._classify_layers
_fatal_findings = _RECORD_CHECKS._fatal_findings
_count_valid_record = _RECORD_CHECKS._count_valid_record
_reproduce_record = _RECORD_CHECKS._reproduce_record
_validate_one_record = _RECORD_CHECKS._validate_one_record
validate_file = _RECORD_CHECKS.validate_file

_SNAPSHOT_CHECKS = _oracle_validate_snapshot.SnapshotChecks(sys.modules[__name__])
_open_beneath = _SNAPSHOT_CHECKS._open_beneath
_stat_identity = _SNAPSHOT_CHECKS._stat_identity
_stat_identity_with_mode = _SNAPSHOT_CHECKS._stat_identity_with_mode
_read_within_limit = _SNAPSHOT_CHECKS._read_within_limit
_capture_pinned_body = _SNAPSHOT_CHECKS._capture_pinned_body
_snapshot_regular_file = _SNAPSHOT_CHECKS._snapshot_regular_file
_open_run_root = _SNAPSHOT_CHECKS._open_run_root

_CAPTURE_CHECKS = _oracle_validate_capture.CaptureChecks(sys.modules[__name__])
_manifest_path_text = _CAPTURE_CHECKS._manifest_path_text
_relative_manifest_parts = _CAPTURE_CHECKS._relative_manifest_parts
_safe_manifest_path = _CAPTURE_CHECKS._safe_manifest_path
_is_sha256_hex = _CAPTURE_CHECKS._is_sha256_hex
_load_run_manifest = _CAPTURE_CHECKS._load_run_manifest
_manifest_file_entries = _CAPTURE_CHECKS._manifest_file_entries
_manifest_entry_fields = _CAPTURE_CHECKS._manifest_entry_fields
_verify_captured_file = _CAPTURE_CHECKS._verify_captured_file
_capture_one_manifested_file = _CAPTURE_CHECKS._capture_one_manifested_file
_capture_manifested_files = _CAPTURE_CHECKS._capture_manifested_files
_run_tree_identity = _CAPTURE_CHECKS._run_tree_identity
_verify_run_tree_unchanged = _CAPTURE_CHECKS._verify_run_tree_unchanged
_manifest_payload_entries = _CAPTURE_CHECKS._manifest_payload_entries
_manifest_membership_errors = _CAPTURE_CHECKS._manifest_membership_errors
_authenticate_manifest_from_root = _CAPTURE_CHECKS._authenticate_manifest_from_root
authenticate_manifest = _CAPTURE_CHECKS.authenticate_manifest

_MANIFEST_CHECKS = _oracle_validate_manifest.ManifestChecks(sys.modules[__name__])
_read_manifest_header = _MANIFEST_CHECKS._read_manifest_header
_header_field_errors = _MANIFEST_CHECKS._header_field_errors
_seed_field_errors = _MANIFEST_CHECKS._seed_field_errors
_header_identity_errors = _MANIFEST_CHECKS._header_identity_errors
_commit_identity_errors = _MANIFEST_CHECKS._commit_identity_errors
_declared_families_block = _MANIFEST_CHECKS._declared_families_block
_declared_family_count_errors = _MANIFEST_CHECKS._declared_family_count_errors
_run_file_layout = _MANIFEST_CHECKS._run_file_layout
_file_layout_entry = _MANIFEST_CHECKS._file_layout_entry
_family_file_pairing_errors = _MANIFEST_CHECKS._family_file_pairing_errors
_expected_family_files = _MANIFEST_CHECKS._expected_family_files
_family_summaries = _MANIFEST_CHECKS._family_summaries
_expected_runtime_set = _MANIFEST_CHECKS._expected_runtime_set
_probe_matches = _MANIFEST_CHECKS._probe_matches
_availability_probe_errors = _MANIFEST_CHECKS._availability_probe_errors
_declared_probe_runtime = _MANIFEST_CHECKS._declared_probe_runtime
_availability_rollup_errors = _MANIFEST_CHECKS._availability_rollup_errors
_bound_runtime_names = _MANIFEST_CHECKS._bound_runtime_names
_unbound_runtime_names = _MANIFEST_CHECKS._unbound_runtime_names
_availability_block_errors = _MANIFEST_CHECKS._availability_block_errors
_runtime_name_errors = _MANIFEST_CHECKS._runtime_name_errors
_manifest_metadata_errors = _MANIFEST_CHECKS._manifest_metadata_errors
_manifest_note_errors = _MANIFEST_CHECKS._manifest_note_errors

_MANIFEST_RECORD_CHECKS = _oracle_validate_manifest_records.ManifestRecordChecks(
    sys.modules[__name__]
)
_summary = _MANIFEST_RECORD_CHECKS._summary
_record_index = _MANIFEST_RECORD_CHECKS._record_index
_record_oracle_binding_errors = _MANIFEST_RECORD_CHECKS._record_oracle_binding_errors
_record_seed_errors = _MANIFEST_RECORD_CHECKS._record_seed_errors
_record_availability_errors = _MANIFEST_RECORD_CHECKS._record_availability_errors
_collect_rejection_reasons = _MANIFEST_RECORD_CHECKS._collect_rejection_reasons
_indexes_are_complete = _MANIFEST_RECORD_CHECKS._indexes_are_complete
_family_summary = _MANIFEST_RECORD_CHECKS._family_summary
_group_records_by_family = _MANIFEST_RECORD_CHECKS._group_records_by_family

_RUN_CHECKS = _oracle_validate_run.RunChecks(sys.modules[__name__])
parse_args = _RUN_CHECKS.parse_args
validate_run = _RUN_CHECKS.validate_run
validate_run_snapshot = _RUN_CHECKS.validate_run_snapshot
_snapshot_expected_commit = _RUN_CHECKS._snapshot_expected_commit
_snapshot_metadata_errors = _RUN_CHECKS._snapshot_metadata_errors
main = _RUN_CHECKS.main


if __package__:
    _expose_package_sibling(__name__)


if __name__ == "__main__":
    sys.exit(main())
