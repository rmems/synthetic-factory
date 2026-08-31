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
import ctypes
import errno
import fcntl
import hashlib
import json
import os
import secrets
import shutil
import stat
import sys
from pathlib import Path

from oracle_grounded import canon, families, oracles, record
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
    parser.add_argument("--list-families", action="store_true")
    return parser.parse_args(argv)


def generate_family(
    family,
    count,
    seed,
    round_number,
    commit,
    dirty,
    require_runtime,
    environ=None,
):
    """Build ``count`` records for one family, split by verdict."""
    accepted = []
    rejected = []
    errors = []
    for index in range(count):
        try:
            item = record.build_record(
                family,
                index,
                seed=seed,
                round_number=round_number,
                commit=commit,
                dirty=dirty,
                environ=environ,
            )
        except (oracles.OracleError, record.GenerationError) as exc:
            errors.append(f"{family}#{index}: {type(exc).__name__}: {exc}")
            continue
        layers = record.classify(item, require_named_runtime=require_runtime)
        fatal = layers["envelope"] + layers["status"]
        if fatal:
            errors.append(
                f"{family}#{index}: generated record failed its envelope: " + "; ".join(fatal)
            )
            continue
        if item["validation"]["status"] == "accepted" and not layers["family"]:
            accepted.append(item)
        else:
            rejected.append(item)
    return accepted, rejected, errors


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "".join(canon.dumps_record(item) + "\n" for item in records)
    encoded = body.encode("utf-8")
    path.write_text(body, encoding="utf-8")
    return hashlib.sha256(encoded).hexdigest(), len(encoded)


def summarize(records):
    scored = [
        item["validation"]["candidate_prediction_correct"]
        for item in records
        if item["validation"]["candidate_prediction_correct"] is not None
    ]
    return {
        "records": len(records),
        "candidate_scored": len(scored),
        "candidate_correct": sum(1 for value in scored if value),
    }


def _raw_containment_error(resolved, out_dir):
    """The refusal for a fully resolved path inside ``outputs/raw/``, or None."""
    raw_root = Path(os.path.realpath(RAW_TREE))
    if resolved == raw_root or raw_root in resolved.parents:
        return (
            f"{out_dir} resolves into the immutable raw tree {RAW_TREE}; "
            "outputs/raw/ is never a generation destination"
        )
    return None


def _raw_destination_error(out_dir):
    """Why ``out_dir`` may not be used, or None. Runs before anything is written.

    ``reserve_run`` creates a sibling lock before the staging tree exists, so a
    destination beneath the repository's immutable ``outputs/raw/`` tree must be
    refused before the reservation -- including a path that only resolves there
    through symlinks.  An unresolvable path is refused rather than trusted.
    """
    try:
        resolved = Path(os.path.realpath(out_dir))
        return _raw_containment_error(resolved, out_dir)
    except (OSError, ValueError) as exc:
        return f"could not resolve {out_dir} against the immutable raw tree: {type(exc).__name__}"


def _pinned_parent_descriptor(parent, out_dir):
    """Open and authenticate the run's parent directory for the transaction.

    ``_raw_destination_error`` checks the path before anything exists, but a
    non-cooperating process can swap a checked ancestor for a symlink into
    ``outputs/raw/`` after that check returns.  Every later write of the
    transaction goes through this descriptor, so this authentication is the
    one that counts: the kernel reports where the descriptor really landed,
    and a parent inside the raw tree is refused no matter what the path
    components claimed.  Platforms without ``/proc`` descriptor resolution
    fail closed, exactly like the ``renameat2`` publication point.
    """
    parent_fd = os.open(
        parent,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        try:
            true_parent = Path(os.readlink(f"/proc/self/fd/{parent_fd}"))
        except OSError as exc:
            raise OSError(
                errno.ENOSYS,
                "cannot authenticate the run parent without /proc descriptor resolution",
            ) from exc
        error = _raw_containment_error(true_parent, out_dir)
        if error is not None:
            raise OSError(errno.EACCES, error)
    except BaseException:
        os.close(parent_fd)
        raise
    return parent_fd


def _locked_lock_descriptor(lock_path, dir_fd=None):
    """Open, authenticate, and exclusively lock one reservation file.

    The descriptor is closed on any failure after the open; the open itself
    propagates without a descriptor to clean up.  With ``dir_fd`` the lock
    name is resolved relative to an already-authenticated parent descriptor,
    so a racing ancestor swap cannot redirect the lock.
    """
    descriptor = os.open(
        lock_path,
        os.O_CREAT | os.O_RDWR | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
        0o600,
        dir_fd=dir_fd,
    )
    try:
        lock_stat = os.fstat(descriptor)
        if not stat.S_ISREG(lock_stat.st_mode) or lock_stat.st_nlink != 1:
            raise OSError(errno.EINVAL, "reservation lock is not a regular file")
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(descriptor)
        raise
    return descriptor


def reserve_run(out_dir):
    """Hold a kernel lock for this output name for the full transaction.

    Returns ``(lock_descriptor, parent_fd)``; the caller owns both.  The
    reservation lock, the staging tree, and the publication rename all go
    through ``parent_fd``, so an ancestor swapped for a symlink after the
    static destination check can no longer redirect any of those writes.
    """
    parent = out_dir.parent
    parent.mkdir(parents=True, exist_ok=True)
    parent_fd = _pinned_parent_descriptor(parent, out_dir)
    stem = out_dir.name or "oracle-run"
    lock_name = f".{stem}.oracle-generate.lock"
    try:
        try:
            descriptor = _locked_lock_descriptor(lock_name, dir_fd=parent_fd)
        except (BlockingIOError, FileExistsError) as exc:
            raise FileExistsError(
                f"another generation owns reservation {parent / lock_name}"
            ) from exc
        try:
            exists = True
            if out_dir.name:
                try:
                    os.lstat(out_dir.name, dir_fd=parent_fd)
                except FileNotFoundError:
                    exists = False
            if exists:
                raise FileExistsError(f"refusing to overwrite existing run {out_dir}")
        except BaseException:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)
            raise
    except BaseException:
        os.close(parent_fd)
        raise
    return descriptor, parent_fd


def _directory_identity(path):
    state = os.lstat(path)
    if not stat.S_ISDIR(state.st_mode):
        raise OSError(errno.ENOTDIR, "publication source is not a directory", os.fspath(path))
    return state.st_dev, state.st_ino


def _rename_noreplace(source, destination):
    """Linux atomic rename that never replaces ``destination``."""
    if not sys.platform.startswith("linux"):
        raise OSError(errno.ENOSYS, "atomic no-replace publication is unavailable")
    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise OSError(errno.ENOSYS, "renameat2(RENAME_NOREPLACE) is unavailable")
    renameat2.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    renameat2.restype = ctypes.c_int
    result = renameat2(
        AT_FDCWD,
        os.fsencode(source),
        AT_FDCWD,
        os.fsencode(destination),
        RENAME_NOREPLACE,
    )
    if result != 0:
        error = ctypes.get_errno() or errno.EIO
        raise OSError(error, os.strerror(error), os.fspath(destination))


def publish_noreplace(staging, out_dir, expected_identity=None):
    """Publish a sibling staging tree without ever replacing a destination.

    POSIX ``rename`` permits replacing an empty directory, so the reservation
    check alone cannot defend against a non-cooperating writer racing in after
    it.  Linux ``renameat2(RENAME_NOREPLACE)`` makes the publication point itself
    fail with ``EEXIST``.  Platforms/libcs without that primitive fail closed.
    """
    expected_identity = expected_identity or _directory_identity(staging)
    if _directory_identity(staging) != expected_identity:
        raise OSError(errno.ESTALE, "publication source identity changed before rename")
    _rename_noreplace(staging, out_dir)
    published_identity = _directory_identity(out_dir)
    if published_identity != expected_identity:
        # A non-cooperating writer swapped its own directory in after our
        # rename. Move the imposter aside so the run name is not left
        # claiming our authentication, but never delete it: that inode is
        # known NOT to be the staging tree, so its content belongs to
        # someone else and destroying it would turn a detected race into
        # data loss. Publication still fails loudly.
        quarantine = out_dir.with_name(
            f".{out_dir.name or 'oracle-run'}.rejected-{secrets.token_hex(8)}"
        )
        try:
            _rename_noreplace(out_dir, quarantine)
        except OSError:
            pass
        raise OSError(
            errno.ESTALE,
            "published directory identity did not match the authenticated staging tree",
        )


def _cleanup_staging(staging, staging_identity):
    """Remove only the staging inode whose identity was authenticated.

    If a non-cooperating writer renamed our staging tree away and created
    its own directory at the same path, that replacement is not ours to
    delete; leave it and let the failed transaction report the problem.
    """
    if staging is None or staging_identity is None:
        return
    try:
        if _directory_identity(staging) == staging_identity:
            shutil.rmtree(staging)
    except OSError:
        # Already gone, or replaced by something that is not our directory.
        pass


def build_manifest(args, selected, availability, commit, dirty, generated, files):
    per_family = {}
    all_errors = []
    any_publishable = False
    for family in selected:
        accepted, rejected, errors = generated[family]
        all_errors.extend(errors)
        if any(item["validation"]["publishable"] for item in accepted + rejected):
            any_publishable = True
        per_family[family] = {
            "proposed": args.count,
            "accepted": summarize(accepted),
            "rejected": {
                "records": len(rejected),
                "reasons": sorted(
                    {reason for item in rejected for reason in item["validation"]["reasons"]}
                ),
            },
            "oracle": {
                "requested_runtime": list(families.spec_for(family).runtimes),
                "implementation": (
                    accepted[0]["oracle"]["implementation"]
                    if accepted
                    else (rejected[0]["oracle"]["implementation"] if rejected else None)
                ),
            },
        }
    if any_publishable:
        note = (
            "Counts describe this run only. Some records were measured through "
            "the named-runtime protocol and are publishable; check each "
            "record's own validation.publishable and validation.publishable_reason "
            "for the authoritative per-record determination."
        )
    else:
        note = (
            "Counts describe this run only. A reference-implementation oracle "
            "measures a real model but is not the named runtime; no record here "
            "is publishable as a measurement of the named runtime."
        )
    return {
        "schema": record.SCHEMA_ID,
        "round": args.round_number,
        "seed": args.seed,
        "count_per_family": args.count,
        "families": per_family,
        "oracle_commit": commit,
        "oracle_dirty": dirty,
        "module_digest": oracles.module_digest(),
        "oracle_availability": availability,
        "files": files,
        "generation_errors": all_errors,
        "note": note,
    }


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
    return None


def _select_families(args):
    """The requested families, de-duplicated in order. (selected, exit code)."""
    selected = list(dict.fromkeys(args.family_names or families.FAMILY_NAMES))
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


def _stamp_contradicts_checkout(commit, availability):
    """Whether an explicit --oracle-commit may not be trusted.

    A bound named runtime can make this run's records publishable, so an
    explicit --oracle-commit may not silently name a different revision than
    the checkout that actually supplied module_digest and ran the oracle. When
    git cannot resolve the checkout at all, fall back to trusting the caller's
    stamp, same as the no-runtime-bound case.
    """
    if not any(probe["bound"] for probe in availability["runtimes"]):
        return False
    checkout_commit, _checkout_dirty = oracles.resolve_commit()
    return checkout_commit != "unknown" and checkout_commit != commit


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
                f"checked-out HEAD ({checkout_commit}); a bound named runtime can "
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


def main(argv=None):
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    if args.list_families:
        for name in families.FAMILY_NAMES:
            print(name)
        return 0

    argument_error = _argument_errors(args)
    if argument_error is not None:
        return argument_error

    selected, selection_error = _select_families(args)
    if selection_error is not None:
        return selection_error

    availability = oracles.availability_report(_requested_runtimes(selected))
    if args.require_runtime and not availability["all_bound"]:
        print(
            "oracle_generate: --require-runtime was passed but these oracles are "
            f"not bound: {', '.join(availability['unbound'])}",
            file=sys.stderr,
        )
        return 3

    commit, dirty, stamp_error = _resolve_stamp(args, availability)
    if stamp_error is not None:
        return stamp_error

    out_dir = Path(args.out_dir)
    raw_error = _raw_destination_error(out_dir)
    if raw_error is not None:
        print(f"oracle_generate: {raw_error}", file=sys.stderr)
        return 2
    try:
        lock_descriptor, parent_fd = reserve_run(out_dir)
    except (FileExistsError, NotADirectoryError, OSError) as exc:
        print(f"oracle_generate: {exc}", file=sys.stderr)
        return 2

    staging = None
    staging_identity = None
    manifest_text = None
    published = False
    try:
        # Build every family before creating a publishable tree.  Any oracle
        # failure aborts the whole run instead of authenticating a partial run.
        generated = {}
        all_errors = []
        for family in selected:
            generated[family] = generate_family(
                family,
                args.count,
                args.seed,
                args.round_number,
                commit,
                dirty,
                args.require_runtime,
            )
            all_errors.extend(generated[family][2])
        if all_errors:
            for error in all_errors:
                print(f"oracle_generate: {error}", file=sys.stderr)
            return 1

        # Create and address the staging tree through the authenticated parent
        # descriptor: every write below resolves through the pinned directory,
        # so an ancestor swapped for a symlink after the reservation cannot
        # redirect the staging files or the publication rename.
        pinned_parent = Path(f"/proc/self/fd/{parent_fd}")
        staging_name = f".{out_dir.name or 'oracle-run'}.staging-{secrets.token_hex(8)}"
        os.mkdir(staging_name, mode=0o700, dir_fd=parent_fd)
        staging = pinned_parent / staging_name
        staging_identity = _directory_identity(staging)
        files = {}
        total_bytes = 0
        oversized = []
        for family in selected:
            accepted, rejected, _errors = generated[family]
            for verdict, items in (("accepted", accepted), ("rejected", rejected)):
                relative = Path(family) / f"{verdict}-r{args.round_number:02d}.jsonl"
                digest, byte_count = write_jsonl(staging / relative, items)
                files[relative.as_posix()] = {
                    "sha256": digest,
                    "records": len(items),
                }
                total_bytes += byte_count
                if byte_count > MAX_JSONL_BYTES:
                    oversized.append(
                        f"{relative.as_posix()} is {byte_count} bytes, exceeding the "
                        f"validator's {MAX_JSONL_BYTES}-byte per-file limit"
                    )
        manifest = build_manifest(
            args,
            selected,
            availability,
            commit,
            dirty,
            generated,
            files,
        )
        # The validator counts every regular file -- the manifest included --
        # against its per-run limit, so serialize it now and count it too.
        manifest_text = json.dumps(canon.normalize(manifest), indent=2, sort_keys=True)
        manifest_bytes = len(manifest_text.encode("utf-8")) + 1  # trailing newline
        if manifest_bytes > MAX_MANIFEST_BYTES:
            oversized.append(
                f"manifest.json is {manifest_bytes} bytes, exceeding the "
                f"validator's {MAX_MANIFEST_BYTES}-byte manifest limit"
            )
        total_bytes += manifest_bytes
        if total_bytes > MAX_RUN_BYTES:
            oversized.append(
                f"the run is {total_bytes} bytes including the manifest, exceeding "
                f"the validator's {MAX_RUN_BYTES}-byte per-run limit"
            )
        if oversized:
            # oracle_validate.py would always reject this run anyway; fail
            # before publication instead of letting it exit successfully.
            for error in oversized:
                print(f"oracle_generate: {error}", file=sys.stderr)
            return 1
        (staging / "manifest.json").write_text(
            manifest_text + "\n",
            encoding="utf-8",
        )
        # The publication point itself is no-replace; a non-cooperating writer
        # that races the reservation cannot have its directory overwritten.
        # The destination is addressed through the pinned parent as well.
        publish_noreplace(staging, pinned_parent / out_dir.name, staging_identity)
        staging = None
        published = True
    except (OSError, TypeError, ValueError) as exc:
        print(
            f"oracle_generate: transaction failed before publication: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1
    finally:
        try:
            # Cleanup addresses the staging tree through the still-open parent
            # descriptor, so it must run before that descriptor is closed.
            _cleanup_staging(staging, staging_identity)
        finally:
            fcntl.flock(lock_descriptor, fcntl.LOCK_UN)
            os.close(lock_descriptor)
            os.close(parent_fd)
    if published:
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
    return 1


if __name__ == "__main__":
    sys.exit(main())
