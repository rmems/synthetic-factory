#!/usr/bin/env python3
"""Generate oracle-grounded neuromorphic records (issue #77).

For each dataset family the generator proposes scenarios and interventions and
the family's oracle adapter measures the outcome. Accepted and rejected records
are written to separate files so curation is fail-closed by construction: a
consumer that reads only `accepted-*.jsonl` never sees a record whose oracle
result is missing, unattributed, or failing its family's invariants.

Nothing is overwritten. A run whose output files already exist exits nonzero.

Usage:
  python3 pipelines/oracle_generate.py [options] <out_dir>

Options:
  --family NAME         Restrict to one family (repeatable). Default: all five.
  --count N             Proposals per family (default 8).
  --seed N              Master seed (default 20260823).
  --round N             Round number stamped into ids and filenames (default 1).
  --oracle-commit SHA   Pin the commit stamped into records instead of asking git.
  --oracle-dirty        Force the recorded dirty flag on.
  --no-oracle-dirty     Force the recorded dirty flag off.
  --require-runtime     Refuse to write unless every named runtime is bound.
  --list-families       Print the family names and exit.
"""

import argparse
import errno
import fcntl
import json
import os
import secrets
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("oracle_generate")
    from .operator_paths import confine_named
    from .oracle_grounded import (
        canon,
        families,
        native_profiles as _native_profiles,
        native_runtime as _native_runtime,
        oracles,
        record as _record,
        rng as _rng,
    )
    from .oracle_grounded.generation_output import (
        _output_descriptor,
        _verify_staged_manifest,
        _verify_staged_payloads,
        write_jsonl,
    )
    from .oracle_validate import MAX_JSONL_BYTES, MAX_MANIFEST_BYTES, MAX_RUN_BYTES
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_generate"
    )
    from operator_paths import confine_named
    from oracle_grounded import (
        canon,
        families,
        native_profiles as _native_profiles,
        native_runtime as _native_runtime,
        oracles,
        record as _record,
        rng as _rng,
    )
    from oracle_grounded.generation_output import (
        _output_descriptor,
        _verify_staged_manifest,
        _verify_staged_payloads,
        write_jsonl,
    )
    from oracle_validate import MAX_JSONL_BYTES, MAX_MANIFEST_BYTES, MAX_RUN_BYTES

DEFAULT_SEED = 20260823
DEFAULT_COUNT = 8
MAX_COUNT = 100_000
MAX_RUN_RECORDS = 100_000
MAX_ROUND = 99_999_999
AT_FDCWD = -100
RENAME_NOREPLACE = 1
# The immutable raw tree (AGENTS.md): never a generation destination, and
# never the parent of one -- even the sibling reservation lock would violate it.
RAW_TREE = oracles.REPO_ROOT / "outputs" / "raw"
# Re-exported for the delegated generation classes, which read these through
# ``self.api`` -- the live module namespace of this facade.
record = _record
native_profiles = _native_profiles
native_runtime = _native_runtime
rng = _rng

if __package__:
    from .oracle_generate_fs import GenerationFilesystem
    from .oracle_generate_parents import GenerationParents
    from .oracle_generate_prepare import GenerationPreparation
    from .oracle_generate_publish import GenerationPublish
    from .oracle_generate_records import FamilyJob, GenerationRecords, RunOutputs
else:
    from oracle_generate_fs import GenerationFilesystem
    from oracle_generate_parents import GenerationParents
    from oracle_generate_prepare import GenerationPreparation
    from oracle_generate_publish import GenerationPublish
    from oracle_generate_records import FamilyJob, GenerationRecords, RunOutputs

_GENERATION_FS = GenerationFilesystem(sys.modules[__name__])
_GENERATION_PARENTS = GenerationParents(sys.modules[__name__])
_GENERATION_PUBLISH = GenerationPublish(sys.modules[__name__])
_GENERATION_RECORDS = GenerationRecords(sys.modules[__name__])
_PREPARATION = GenerationPreparation(sys.modules[__name__])
_argument_errors = _PREPARATION._argument_errors
_assert_destination_absent = _GENERATION_FS._assert_destination_absent
_authenticate_parent_descriptor = _GENERATION_PARENTS._authenticate_parent_descriptor
_bind_runtimes = _PREPARATION._bind_runtimes
_checkout_stamp = _PREPARATION._checkout_stamp
_claim_reservation_lock = _GENERATION_FS._claim_reservation_lock
_claimed_reservation = _GENERATION_FS._claimed_reservation
_cleanup_parent_descriptor = _GENERATION_PUBLISH._cleanup_parent_descriptor
_cleanup_staging = _GENERATION_PUBLISH._cleanup_staging
_create_pinned_parent = _GENERATION_PARENTS._create_pinned_parent
_directory_identity = _GENERATION_FS._directory_identity
_explicit_stamp = _PREPARATION._explicit_stamp
_locked_lock_descriptor = _GENERATION_FS._locked_lock_descriptor
_open_created_parent = _GENERATION_PARENTS._open_created_parent
_pinned_parent_descriptor = _GENERATION_PARENTS._pinned_parent_descriptor
_prepare_run = _PREPARATION._prepare_run
_quarantine_mismatch = _GENERATION_PUBLISH._quarantine_mismatch
_raw_containment_error = _GENERATION_FS._raw_containment_error
_raw_destination_error = _GENERATION_FS._raw_destination_error
_rename_noreplace = _GENERATION_PUBLISH._rename_noreplace
_requested_runtimes = _PREPARATION._requested_runtimes
_reserve_destination = _PREPARATION._reserve_destination
_resolve_stamp = _PREPARATION._resolve_stamp
_select_families = _PREPARATION._select_families
_stamp_contradicts_checkout = _PREPARATION._stamp_contradicts_checkout
_verify_requested_publication = _GENERATION_FS._verify_requested_publication
publish_noreplace = _GENERATION_PUBLISH.publish_noreplace
reserve_run = _GENERATION_FS.reserve_run
_charge_record = _GENERATION_RECORDS._charge_record
_generated_implementation = _GENERATION_RECORDS._generated_implementation
build_manifest = _GENERATION_RECORDS.build_manifest
generate_family = _GENERATION_RECORDS.generate_family
summarize = _GENERATION_RECORDS.summarize


_PATH_ARGUMENTS = {
    "out_dir": "out_dir",
    "oracle_rust_bin": "--oracle-rust-bin",
}


@dataclass(frozen=True)
class PreparedRun:
    """The validated inputs and reservation one generation transaction needs."""

    selected: list
    availability: dict
    commit: object
    dirty: object
    out_dir: Path
    lock_descriptor: int
    parent_fd: int


def _argument_parser():
    parser = argparse.ArgumentParser(add_help=True, description=__doc__)
    parser.add_argument("out_dir", nargs="?")
    parser.add_argument("--family", action="append", dest="family_names")
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--round", type=int, default=1, dest="round_number")
    parser.add_argument("--oracle-commit", dest="oracle_commit")
    parser.add_argument("--oracle-dirty", dest="oracle_dirty", action="store_true", default=None)
    parser.add_argument("--no-oracle-dirty", dest="oracle_dirty", action="store_false")
    parser.add_argument("--require-runtime", action="store_true")
    parser.add_argument("--backend", choices=("reference", "rust"), default="reference")
    parser.add_argument("--oracle-rust-bin")
    parser.add_argument("--list-families", action="store_true")
    return parser


def parse_args(argv):
    return _argument_parser().parse_args(argv)


def _generate_selected(selected, job):
    generated = {}
    for family in selected:
        generated[family] = generate_family(family, job)
        errors = generated[family][2]
        if errors:
            for error in errors:
                print(f"oracle_generate: {error}", file=sys.stderr)
            return None
    return generated


def _create_staging(out_dir, parent_fd):
    pinned_parent = Path(f"/proc/self/fd/{parent_fd}")
    staging_name = f".{out_dir.name or 'oracle-run'}.staging-{secrets.token_hex(8)}"
    os.mkdir(staging_name, mode=0o700, dir_fd=parent_fd)
    staging = pinned_parent / staging_name
    staging_identity = None
    staging_fd = None
    try:
        staging_identity = _directory_identity(staging)
        staging_fd = os.open(
            staging_name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd
        )
        opened = os.fstat(staging_fd)
        if (opened.st_dev, opened.st_ino) != staging_identity:
            raise OSError(errno.ESTALE, "staging identity changed before opening")
        return pinned_parent, staging, staging_identity, staging_fd
    except BaseException:
        if staging_fd is not None:
            os.close(staging_fd)
        _cleanup_staging(staging, staging_identity, parent_fd)
        raise


def _write_payloads(round_number, selected, generated, staging_fd):
    files = {}
    total_bytes = 0
    oversized = []
    for family in selected:
        accepted, rejected, _errors = generated[family]
        for verdict, items in (("accepted", accepted), ("rejected", rejected)):
            relative = Path(family) / f"{verdict}-r{round_number:02d}.jsonl"
            digest, byte_count = write_jsonl(relative, items, root_fd=staging_fd)
            files[relative.as_posix()] = {"sha256": digest, "records": len(items)}
            total_bytes += byte_count
            if byte_count > MAX_JSONL_BYTES:
                oversized.append(
                    f"{relative.as_posix()} is {byte_count} bytes, exceeding the "
                    f"validator's {MAX_JSONL_BYTES}-byte per-file limit"
                )
    return files, total_bytes, oversized


def _manifest_text(job, outputs, total_bytes):
    manifest = build_manifest(job, outputs)
    text = json.dumps(canon.normalize(manifest), indent=2, sort_keys=True)
    manifest_bytes = len(text.encode("utf-8")) + 1
    oversized = []
    if manifest_bytes > MAX_MANIFEST_BYTES:
        oversized.append(
            f"manifest.json is {manifest_bytes} bytes, exceeding the "
            f"validator's {MAX_MANIFEST_BYTES}-byte manifest limit"
        )
    run_bytes = total_bytes + manifest_bytes
    if run_bytes > MAX_RUN_BYTES:
        oversized.append(
            f"the run is {run_bytes} bytes including the manifest, exceeding "
            f"the validator's {MAX_RUN_BYTES}-byte per-run limit"
        )
    return text, oversized


def _write_manifest(staging_fd, manifest_text):
    descriptor = _output_descriptor(Path("manifest.json"), staging_fd)
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
        output.write(manifest_text + "\n")


def _transaction_error(exc, published):
    if published:
        phase = "after publication; requested destination could not be authenticated"
    else:
        phase = "before publication"
    print(
        f"oracle_generate: transaction failed {phase}: {type(exc).__name__}: {exc}",
        file=sys.stderr,
    )


def _release_reservation(lock_descriptor, parent_fd):
    fcntl.flock(lock_descriptor, fcntl.LOCK_UN)
    os.close(lock_descriptor)
    os.close(parent_fd)


def _run_transaction(args, prepared):
    staging = None
    staging_identity = None
    staging_fd = None
    manifest_text = None
    published = False
    job = FamilyJob(
        count=args.count,
        seed=args.seed,
        round_number=args.round_number,
        commit=prepared.commit,
        dirty=prepared.dirty,
        require_runtime=args.require_runtime,
        environ=args.runtime_environ,
        backend=args.backend,
        byte_budget=[0],
    )
    try:
        generated = _generate_selected(prepared.selected, job)
        if generated is None:
            return 1, None
        pinned_parent, staging, staging_identity, staging_fd = _create_staging(
            prepared.out_dir, prepared.parent_fd
        )
        files, total_bytes, oversized = _write_payloads(
            job.round_number, prepared.selected, generated, staging_fd
        )
        outputs = RunOutputs(
            prepared.selected, prepared.availability, generated, files
        )
        manifest_text, manifest_oversized = _manifest_text(job, outputs, total_bytes)
        oversized.extend(manifest_oversized)
        if oversized:
            for error in oversized:
                print(f"oracle_generate: {error}", file=sys.stderr)
            return 1, None
        _write_manifest(staging_fd, manifest_text)
        _verify_staged_payloads(staging_fd, files, MAX_JSONL_BYTES)
        _verify_staged_manifest(staging_fd, (manifest_text + "\n").encode("utf-8"))
        _verify_requested_publication(prepared.out_dir, prepared.parent_fd)
        publish_noreplace(staging, pinned_parent / prepared.out_dir.name, staging_identity)
        staging = None
        published = True
        _verify_requested_publication(prepared.out_dir, prepared.parent_fd, staging_identity)
    except (OSError, TypeError, ValueError) as exc:
        _transaction_error(exc, published)
        return 1, None
    finally:
        try:
            if staging_fd is not None:
                os.close(staging_fd)
            _cleanup_staging(staging, staging_identity, prepared.parent_fd)
        finally:
            _release_reservation(prepared.lock_descriptor, prepared.parent_fd)
    return (0, manifest_text) if published else (1, None)


def _print_manifest(manifest_text, out_dir):
    try:
        print(manifest_text)
    except OSError as exc:
        print(
            f"oracle_generate: run was published at {out_dir}, but the manifest "
            f"could not be written to stdout: {type(exc).__name__}",
            file=sys.stderr,
        )
        return 1
    return 0


def main(argv=None):
    parser = _argument_parser()
    args = parser.parse_args(list(sys.argv[1:] if argv is None else argv))
    if args.list_families:
        for name in families.FAMILY_NAMES:
            print(name)
        return 0
    paths = confine_named(parser, args, _PATH_ARGUMENTS)
    args.out_dir = paths["out_dir"]
    args.oracle_rust_bin = paths["oracle_rust_bin"]
    context, error = _prepare_run(args)
    if error is not None:
        return error
    status, manifest_text = _run_transaction(args, context)
    if status != 0:
        return status
    return _print_manifest(manifest_text, Path(args.out_dir))


if __package__:
    _expose_package_sibling(__name__)


if __name__ == "__main__":
    sys.exit(main())
