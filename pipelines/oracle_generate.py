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
from pathlib import Path

from oracle_grounded import canon, families, oracles, record as _record, rng
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
record = _record

if __package__:
    from .oracle_generate_fs import GenerationFilesystem
    from .oracle_generate_records import GenerationRecords
else:
    from oracle_generate_fs import GenerationFilesystem
    from oracle_generate_records import GenerationRecords

_GENERATION_FS = GenerationFilesystem(sys.modules[__name__])
_GENERATION_RECORDS = GenerationRecords(sys.modules[__name__])
_authenticate_parent_descriptor = _GENERATION_FS._authenticate_parent_descriptor
_cleanup_staging = _GENERATION_FS._cleanup_staging
_create_pinned_parent = _GENERATION_FS._create_pinned_parent
_directory_identity = _GENERATION_FS._directory_identity
_locked_lock_descriptor = _GENERATION_FS._locked_lock_descriptor
_open_created_parent = _GENERATION_FS._open_created_parent
_pinned_parent_descriptor = _GENERATION_FS._pinned_parent_descriptor
_raw_containment_error = _GENERATION_FS._raw_containment_error
_raw_destination_error = _GENERATION_FS._raw_destination_error
_rename_noreplace = _GENERATION_FS._rename_noreplace
_verify_requested_publication = _GENERATION_FS._verify_requested_publication
publish_noreplace = _GENERATION_FS.publish_noreplace
reserve_run = _GENERATION_FS.reserve_run
_charge_record = _GENERATION_RECORDS._charge_record
_generated_implementation = _GENERATION_RECORDS._generated_implementation
build_manifest = _GENERATION_RECORDS.build_manifest
generate_family = _GENERATION_RECORDS.generate_family
summarize = _GENERATION_RECORDS.summarize


def parse_args(argv):
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
    return parser.parse_args(argv)






































def _argument_errors(args):
    """Presence and range checks on the parsed arguments. Exit code, or None."""
    if not args.out_dir:
        print("oracle_generate: an output directory is required", file=sys.stderr)
        return 2
    if not 1 <= args.count <= MAX_COUNT:
        print(
            f"oracle_generate: --count must be in [1, {MAX_COUNT}]",
            file=sys.stderr,
        )
        return 2
    if not 1 <= args.round_number <= MAX_ROUND:
        print(
            f"oracle_generate: --round must be in [1, {MAX_ROUND}]",
            file=sys.stderr,
        )
        return 2
    if not 0 <= args.seed <= rng.MAX_SEED:
        print(
            f"oracle_generate: --seed must be in [0, {rng.MAX_SEED}] (a 64-bit integer)",
            file=sys.stderr,
        )
        return 2
    return None


def _select_families(args):
    """The requested families, de-duplicated in order. (selected, exit code)."""
    from oracle_grounded.native_profiles import PROFILES
    default = tuple(PROFILES) if args.backend == 'rust' else families.FAMILY_NAMES
    selected = list(dict.fromkeys(args.family_names or default))
    if args.backend == 'rust' and any(name not in PROFILES for name in selected):
        print('oracle_generate: Rust backend supports only encoder and neuron families', file=sys.stderr)
        return None, 2
    unknown = [name for name in selected if name not in families.SPECS]
    if unknown:
        print(f"oracle_generate: unknown families: {', '.join(unknown)}", file=sys.stderr)
        return None, 2
    if args.count * len(selected) > MAX_RUN_RECORDS:
        print(
            "oracle_generate: requested run would contain "
            f"{args.count * len(selected)} records; maximum is {MAX_RUN_RECORDS}",
            file=sys.stderr,
        )
        return None, 2
    return selected, None


def _stamp_contradicts_checkout(commit, _availability):
    """Whether an explicit --oracle-commit may not be trusted.

    Both reference and named-runtime measurements can be publishable, so an
    explicit stamp must name the checkout supplying the implementation.
    """
    checkout_commit, _checkout_dirty = oracles.resolve_commit()
    return (
        oracles.resolve_source_commit(commit) is not None
        and checkout_commit != commit
    )


def _resolve_stamp(args, availability):
    """Resolve the oracle commit and dirty flag. (commit, dirty, exit code)."""
    commit, dirty = args.oracle_commit, args.oracle_dirty
    if commit is None:
        commit, resolved_dirty = oracles.resolve_commit()
        if dirty is None:
            dirty = resolved_dirty
    else:
        if _stamp_contradicts_checkout(commit, availability):
            checkout_commit, _checkout_dirty = oracles.resolve_commit()
            print(
                f"oracle_generate: --oracle-commit {commit!r} does not match the "
                f"checked-out HEAD ({checkout_commit}); oracle measurements can "
                "produce publishable output, so the stamped commit must name the "
                "checkout that supplied the implementation sources",
                file=sys.stderr,
            )
            return None, None, 2
        if dirty is None:
            # An explicit commit stamp must not leave the dirty flag
            # unresolved: a bound named runtime can make this run's records
            # publishable, and null dirty state is not resolved provenance.
            _checkout_commit, checkout_dirty = oracles.resolve_commit()
            if checkout_dirty is not None:
                dirty = checkout_dirty
            elif any(probe["bound"] for probe in availability["runtimes"]):
                print(
                    "oracle_generate: could not resolve the working tree's dirty "
                    "state; a bound named runtime can produce publishable output, "
                    "so pass --oracle-dirty or --no-oracle-dirty explicitly",
                    file=sys.stderr,
                )
                return None, None, 3
    if commit == "unknown":
        print(
            "oracle_generate: could not resolve the oracle commit; pass "
            "--oracle-commit to stamp it explicitly",
            file=sys.stderr,
        )
        return None, None, 3
    resolved_commit = oracles.resolve_source_commit(commit)
    if resolved_commit is None:
        print(
            "oracle_generate: --oracle-commit must resolve to an existing lowercase "
            "40- or 64-hex commit in this source repository",
            file=sys.stderr,
        )
        return None, None, 2
    return resolved_commit, dirty, None


def _requested_runtimes(selected):
    """Every runtime the selected families request, in first-seen order."""
    return tuple(
        dict.fromkeys(
            runtime for family in selected for runtime in families.spec_for(family).runtimes
        )
    )


def _prepare_run(args):
    argument_error = _argument_errors(args)
    if argument_error is not None:
        return None, argument_error
    selected, selection_error = _select_families(args)
    if selection_error is not None:
        return None, selection_error
    args.runtime_environ = {}
    if args.backend == 'rust':
        from oracle_grounded.native_runtime import runtime_environ
        try:
            args.runtime_environ = runtime_environ(args.oracle_rust_bin)
        except oracles.OracleError as exc:
            print(f'oracle_generate: {exc}', file=sys.stderr)
            return None, 3
    availability = oracles.availability_report(_requested_runtimes(selected), args.runtime_environ)
    if args.require_runtime and not availability["all_bound"]:
        print(
            "oracle_generate: --require-runtime was passed but these oracles are "
            f"not bound: {', '.join(availability['unbound'])}",
            file=sys.stderr,
        )
        return None, 3
    commit, dirty, stamp_error = _resolve_stamp(args, availability)
    if stamp_error is not None:
        return None, stamp_error
    out_dir = Path(args.out_dir)
    raw_error = _raw_destination_error(out_dir)
    if raw_error is not None:
        print(f"oracle_generate: {raw_error}", file=sys.stderr)
        return None, 2
    try:
        lock_descriptor, parent_fd = reserve_run(out_dir)
    except OSError as exc:
        print(f"oracle_generate: {exc}", file=sys.stderr)
        return None, 2
    context = (selected, availability, commit, dirty, out_dir, lock_descriptor, parent_fd)
    return context, None


def _generate_selected(args, selected, commit, dirty):
    generated = {}
    byte_budget = [0]
    for family in selected:
        generated[family] = generate_family(
            family,
            args.count,
            args.seed,
            args.round_number,
            commit,
            dirty,
            args.require_runtime,
            byte_budget=byte_budget,
            backend=args.backend,
            environ=args.runtime_environ,
        )
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


def _write_payloads(args, selected, generated, staging_fd):
    files = {}
    total_bytes = 0
    oversized = []
    for family in selected:
        accepted, rejected, _errors = generated[family]
        for verdict, items in (("accepted", accepted), ("rejected", rejected)):
            relative = Path(family) / f"{verdict}-r{args.round_number:02d}.jsonl"
            digest, byte_count = write_jsonl(relative, items, root_fd=staging_fd)
            files[relative.as_posix()] = {"sha256": digest, "records": len(items)}
            total_bytes += byte_count
            if byte_count > MAX_JSONL_BYTES:
                oversized.append(
                    f"{relative.as_posix()} is {byte_count} bytes, exceeding the "
                    f"validator's {MAX_JSONL_BYTES}-byte per-file limit"
                )
    return files, total_bytes, oversized


def _manifest_text(args, selected, availability, commit, dirty, generated, files, total_bytes):
    manifest = build_manifest(args, selected, availability, commit, dirty, generated, files)
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


def _run_transaction(args, context):
    selected, availability, commit, dirty, out_dir, lock_descriptor, parent_fd = context
    staging = None
    staging_identity = None
    staging_fd = None
    manifest_text = None
    published = False
    try:
        generated = _generate_selected(args, selected, commit, dirty)
        if generated is None:
            return 1, None
        pinned_parent, staging, staging_identity, staging_fd = _create_staging(out_dir, parent_fd)
        files, total_bytes, oversized = _write_payloads(args, selected, generated, staging_fd)
        manifest_text, manifest_oversized = _manifest_text(
            args, selected, availability, commit, dirty, generated, files, total_bytes
        )
        oversized.extend(manifest_oversized)
        if oversized:
            for error in oversized:
                print(f"oracle_generate: {error}", file=sys.stderr)
            return 1, None
        _write_manifest(staging_fd, manifest_text)
        _verify_staged_payloads(staging_fd, files, MAX_JSONL_BYTES)
        _verify_staged_manifest(staging_fd, (manifest_text + "\n").encode("utf-8"))
        _verify_requested_publication(out_dir, parent_fd)
        publish_noreplace(staging, pinned_parent / out_dir.name, staging_identity)
        staging = None
        published = True
        _verify_requested_publication(out_dir, parent_fd, staging_identity)
    except (OSError, TypeError, ValueError) as exc:
        _transaction_error(exc, published)
        return 1, None
    finally:
        try:
            if staging_fd is not None:
                os.close(staging_fd)
            _cleanup_staging(staging, staging_identity, parent_fd)
        finally:
            _release_reservation(lock_descriptor, parent_fd)
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
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    if args.list_families:
        for name in families.FAMILY_NAMES:
            print(name)
        return 0
    context, error = _prepare_run(args)
    if error is not None:
        return error
    status, manifest_text = _run_transaction(args, context)
    if status != 0:
        return status
    return _print_manifest(manifest_text, Path(args.out_dir))


if __name__ == "__main__":
    sys.exit(main())
