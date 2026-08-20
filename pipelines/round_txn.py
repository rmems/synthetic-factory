#!/usr/bin/env python3
"""Reserve, stage, validate, and atomically publish one factory round.

Generated data is written outside ``outputs/raw`` first.  A round becomes
visible to frontier readers only when ``ROUND-rNN.complete.json`` is linked
into the factory directory after every staged file has passed validation and
been linked without replacing an existing path.

Usage:
  round_txn.py frontier <factory_dir>
  round_txn.py reserve <factory_dir> --round N --expected N
  round_txn.py publish <factory_dir> --round N --token TOKEN
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import re
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from check_records import check_jsonl  # noqa: E402


MODE_FILE = ".round-marker-mode.json"
BATCH_RE = re.compile(r"^batch-r(\d+)([a-z]*)\.jsonl$")
COMPLETE_RE = re.compile(r"^ROUND-r(\d+)\.complete\.json$")
LEGACY_R1_NAMES = {
    "trajectories.jsonl",
    "final-trajectories.jsonl",
    "pairs.jsonl",
    "preferences.jsonl",
    "episodes.jsonl",
}
FACTORY_QUOTAS = {
    "thalamic-trajectory-factory": 5,
    "multi-agent-ouroboros-swarm": 1,
    "neuromorphic-event-language-bridge": 3,
    "failure-as-fuel-preference-cascade": 3,
    "agentic-coding-trajectory-factory": 2,
    "long-horizon-coding-factory": 2,
    "cascading-error-recovery-factory": 2,
    "tool-use-preference-factory": 3,
    "multi-agent-coordination-factory": 1,
    "safety-calibration-factory": 3,
    "sparse-reward-long-task-factory": 1,
    "eval-harness-trajectory-factory": 2,
    "incident-response-oncall-factory": 2,
    "data-pipeline-repair-factory": 2,
    "git-ops-recovery-factory": 2,
    "browser-tool-use-factory": 2,
    "rag-retrieval-debug-factory": 2,
    "code-review-preference-factory": 3,
    "infra-as-code-factory": 2,
    "api-contract-migration-factory": 2,
    "observability-debug-factory": 2,
    "package-release-factory": 2,
    "flaky-test-quarantine-factory": 2,
    "db-migration-repair-factory": 2,
    "authz-regression-factory": 2,
    "feature-flag-debug-factory": 2,
    "queue-backpressure-factory": 2,
    "websocket-reconnect-factory": 2,
    "csv-excel-ingest-factory": 2,
    "docker-build-cache-factory": 2,
    "k8s-crashloop-factory": 2,
    "log-redaction-factory": 2,
    "rate-limit-backoff-factory": 2,
    "search-index-rebuild-factory": 2,
    "email-webhook-retry-factory": 2,
    "payment-idempotency-factory": 2,
    "graphql-nplusone-factory": 2,
    "ssl-cert-rotation-factory": 2,
    "secret-scan-remediation-factory": 2,
    "monorepo-dep-bump-factory": 2,
    "proto-breaking-change-factory": 2,
    "notebook-to-pipeline-factory": 2,
    "llm-eval-flakiness-factory": 2,
    "prompt-cache-invalidation-factory": 2,
    "agent-memory-compaction-factory": 2,
    "mcp-tool-schema-drift-factory": 2,
    "sandbox-refusal-factory": 3,
    "distributed-lock-factory": 2,
    "cache-stampede-factory": 2,
}

# The original five lanes deliberately allow an operator-selected ``expected``
# count. Every later Grok 4.6 factory is documented with a fixed quota and
# record shape, so it must not be possible to reserve a smaller batch by
# passing a different CLI value.
LEGACY_FACTORY_SLUGS = frozenset(
    {
        "thalamic-trajectory-factory",
        "multi-agent-ouroboros-swarm",
        "neuromorphic-event-language-bridge",
        "failure-as-fuel-preference-cascade",
        "agentic-coding-trajectory-factory",
    }
)
AGENTIC_FACTORY_KINDS = {
    slug: "episode"
    for slug in FACTORY_QUOTAS
    if slug not in LEGACY_FACTORY_SLUGS
}
AGENTIC_FACTORY_KINDS.update(
    {
        "tool-use-preference-factory": "preference",
        "code-review-preference-factory": "preference",
        "multi-agent-coordination-factory": "multi_agent",
        "safety-calibration-factory": "safety_case",
    }
)
NOVEL_COVERAGE_RE = re.compile(
    r"^\s*novel[^%\r\n]*?(\d+(?:\.\d+)?)\s*%", re.IGNORECASE | re.MULTILINE
)


class TransactionError(RuntimeError):
    """A round transaction cannot proceed safely."""


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_exclusive_json(path: Path, payload: dict):
    """Create a JSON file without following or replacing an existing path."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o644)
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        raise


def read_json(path: Path):
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise TransactionError(f"cannot read transaction file {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise TransactionError(f"transaction file must contain an object: {path}")
    return value


def file_sha256(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def valid_legacy_file(path: Path):
    """Return its record count when a legacy JSONL file fully deep-checks."""
    errors, _warnings, _kinds, records = check_jsonl(path, path.name)
    return 0 if errors else records


def discover_legacy_frontier(factory_dir: Path):
    """Highest complete-looking legacy round, ignoring malformed name claims."""
    factory_dir = Path(factory_dir)
    quota = FACTORY_QUOTAS.get(factory_dir.name, 1)
    by_round: dict[int, int] = {}
    for path in factory_dir.glob("*.jsonl"):
        match = BATCH_RE.match(path.name)
        if match:
            round_number = int(match.group(1))
        elif path.name in LEGACY_R1_NAMES:
            round_number = 1
        else:
            continue
        by_round[round_number] = by_round.get(round_number, 0) + valid_legacy_file(path)
    eligible = [round_number for round_number, count in by_round.items() if count >= quota]
    return max(eligible, default=0)


def marker_paths(factory_dir: Path, round_number: int):
    rr = f"{round_number:02d}"
    return {
        "reservation": factory_dir / f"ROUND-r{rr}.reserved.json",
        "publishing": factory_dir / f"ROUND-r{rr}.publishing.json",
        "complete": factory_dir / f"ROUND-r{rr}.complete.json",
    }


def completed_rounds(factory_dir: Path):
    rounds = []
    for path in factory_dir.glob("ROUND-r*.complete.json"):
        match = COMPLETE_RE.match(path.name)
        if not match:
            continue
        payload = read_json(path)
        round_number = int(match.group(1))
        if payload.get("round") != round_number:
            raise TransactionError(
                f"completion marker round mismatch: {path.name} says {payload.get('round')!r}"
            )
        rounds.append(round_number)
    return sorted(set(rounds))


def frontier_status(factory_dir: Path):
    factory_dir = Path(factory_dir).resolve()
    if not factory_dir.is_dir():
        raise TransactionError(f"not a factory directory: {factory_dir}")
    mode_path = factory_dir / MODE_FILE
    if not mode_path.exists():
        baseline = discover_legacy_frontier(factory_dir)
        return {
            "factory": factory_dir.name,
            "mode": "legacy",
            "baseline": baseline,
            "completed_markers": [],
            "highest_flushed": baseline,
            "next_round": baseline + 1,
        }

    mode = read_json(mode_path)
    baseline = mode.get("legacy_baseline")
    if not isinstance(baseline, int) or isinstance(baseline, bool) or baseline < 0:
        raise TransactionError(f"invalid legacy_baseline in {mode_path}")
    markers = completed_rounds(factory_dir)
    highest = baseline
    marker_set = set(markers)
    while highest + 1 in marker_set:
        highest += 1
    noncontiguous = [number for number in markers if number > highest]
    return {
        "factory": factory_dir.name,
        "mode": "marker",
        "baseline": baseline,
        "completed_markers": markers,
        "noncontiguous_markers": noncontiguous,
        "highest_flushed": highest,
        "next_round": highest + 1,
    }


def ensure_marker_mode(factory_dir: Path):
    mode_path = factory_dir / MODE_FILE
    if mode_path.exists():
        return read_json(mode_path)
    payload = {
        "version": 1,
        "created_at": utc_now(),
        "legacy_baseline": discover_legacy_frontier(factory_dir),
        "commit_point": "ROUND-rNN.complete.json",
    }
    try:
        write_exclusive_json(mode_path, payload)
        return payload
    except FileExistsError:
        return read_json(mode_path)


def staging_dir(factory_dir: Path, round_number: int, token: str):
    """Keep staging beside raw so hard-link publication stays one filesystem."""
    try:
        date_dir = factory_dir.parent
        raw_dir = date_dir.parent
        outputs_dir = raw_dir.parent
        if raw_dir.name != "raw" or outputs_dir.name != "outputs":
            raise ValueError
    except (AttributeError, ValueError) as exc:
        raise TransactionError(
            "factory_dir must be outputs/raw/<date>/<factory> for transactional staging"
        ) from exc
    return (
        outputs_dir
        / "staging"
        / date_dir.name
        / factory_dir.name
        / f"r{round_number:02d}-{token}"
    )


def reserve(factory_dir: Path, round_number: int, expected: int):
    factory_dir = Path(factory_dir).resolve()
    if (
        not isinstance(round_number, int)
        or isinstance(round_number, bool)
        or round_number < 1
    ):
        raise TransactionError("round number must be at least 1")
    if not isinstance(expected, int) or isinstance(expected, bool) or expected < 1:
        raise TransactionError("expected record count must be at least 1")
    configured_quota = FACTORY_QUOTAS.get(factory_dir.name)
    if factory_dir.name in AGENTIC_FACTORY_KINDS and expected != configured_quota:
        raise TransactionError(
            f"{factory_dir.name} requires exactly {configured_quota} records; "
            f"got --expected {expected}"
        )
    ensure_marker_mode(factory_dir)
    status = frontier_status(factory_dir)
    if round_number != status["next_round"]:
        raise TransactionError(
            f"round r{round_number:02d} is not the frontier; "
            f"expected r{status['next_round']:02d}"
        )
    paths = marker_paths(factory_dir, round_number)
    for role, path in paths.items():
        if path.exists():
            raise TransactionError(f"{role} path already exists: {path}")

    token = uuid.uuid4().hex
    stage = staging_dir(factory_dir, round_number, token)
    stage.mkdir(parents=True, exist_ok=False)
    payload = {
        "version": 1,
        "factory": factory_dir.name,
        "round": round_number,
        "token": token,
        "expected_records": expected,
        "staging_dir": str(stage),
        "batch_file": f"batch-r{round_number:02d}.jsonl",
        "notes_file": f"NOTES-r{round_number:02d}.md",
        "reserved_at": utc_now(),
    }
    try:
        write_exclusive_json(paths["reservation"], payload)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return payload


def committed_jsonl_paths(factory_dir: Path):
    """Yield only JSONL that is visible as committed data in one factory.

    Before marker mode, every raw JSONL is legacy-visible. Once a factory has
    a marker-mode baseline, a linked batch is visible only when it belongs to
    that declared baseline or has its own completion marker. This deliberately
    excludes files linked by an interrupted publish before its commit marker.
    """
    mode_path = factory_dir / MODE_FILE
    files = sorted(factory_dir.glob("*.jsonl"))
    if not mode_path.exists():
        return files

    mode = read_json(mode_path)
    baseline = mode.get("legacy_baseline")
    if not isinstance(baseline, int) or isinstance(baseline, bool) or baseline < 0:
        raise TransactionError(f"invalid legacy_baseline in {mode_path}")
    complete = set(completed_rounds(factory_dir))
    visible = []
    for path in files:
        match = BATCH_RE.fullmatch(path.name)
        if match is not None:
            round_number = int(match.group(1))
            suffix = match.group(2)
            if round_number <= baseline or (not suffix and round_number in complete):
                visible.append(path)
            continue
        if baseline >= 1 and path.name in LEGACY_R1_NAMES:
            visible.append(path)
    return visible


def committed_ids(factory_dir: Path):
    """Seed the run-wide ID namespace from committed/legacy raw JSONL."""
    seen_ids = {}
    run_dir = factory_dir.parent
    for candidate in sorted(run_dir.iterdir()):
        if not candidate.is_dir():
            continue
        for path in committed_jsonl_paths(candidate):
            # Existing defects are reported by run audits. Here we only need
            # their identity namespace so a new round cannot reuse it.
            check_jsonl(path, path.relative_to(run_dir), seen_ids=seen_ids)
    return seen_ids


@contextlib.contextmanager
def run_publish_lock(factory_dir: Path):
    """Serialize publish validation and the completion marker for one run."""
    path = factory_dir.parent / ".round-publish.lock"
    flags = os.O_RDWR | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags, 0o644)
    except OSError as exc:
        raise TransactionError(f"cannot acquire run publish lock {path}: {exc}") from exc
    with os.fdopen(fd, "a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def validate_agentic_envelope(batch: Path, factory_dir: Path, round_number: int):
    """Return fixed-contract envelope errors for one staged agentic batch."""
    if factory_dir.name not in AGENTIC_FACTORY_KINDS:
        return []
    errors = []
    for lineno, line in enumerate(batch.read_text().splitlines(), 1):
        if not line.strip():
            continue
        # JSON parsing and base shape errors have already been checked by
        # check_jsonl. Keep this narrow pass focused on the factory-specific
        # values that only the transaction layer can know.
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        where = f"{batch.name}:{lineno}"
        if AGENTIC_FACTORY_KINDS[factory_dir.name] == "preference":
            for side_name in ("chosen", "rejected"):
                side = record.get(side_name) if isinstance(record, dict) else None
                if not isinstance(side, dict) or not isinstance(side.get("steps"), list):
                    errors.append(
                        f"{where}: {side_name} must be an episode side with steps"
                    )
        meta = record.get("meta") if isinstance(record, dict) else None
        if not isinstance(meta, dict):
            errors.append(f"{where}: agentic record meta must be an object")
            continue
        if meta.get("factory") != factory_dir.name:
            errors.append(
                f"{where}: meta.factory must be {factory_dir.name!r}"
            )
        meta_round = meta.get("round")
        if (
            not isinstance(meta_round, int)
            or isinstance(meta_round, bool)
            or meta_round != round_number
        ):
            errors.append(f"{where}: meta.round must match reservation r{round_number:02d}")
        if meta.get("generator") != "grok-4.6":
            errors.append(f"{where}: meta.generator must be 'grok-4.6'")
    return errors


def validate_novel_coverage(notes: Path, factory_dir: Path):
    """Require a usable Novel coverage percentage for fixed agentic lanes."""
    if factory_dir.name not in AGENTIC_FACTORY_KINDS:
        return None
    match = NOVEL_COVERAGE_RE.search(notes.read_text())
    if match is None:
        return f"staged notes need a 'Novel coverage: <N>%' line: {notes}"
    value = float(match.group(1))
    if not 0 <= value <= 100:
        return f"staged Novel coverage must be between 0% and 100%: {notes}"
    return None


def validate_stage(
    factory_dir: Path,
    stage: Path,
    round_number: int,
    expected: int,
):
    if not stage.is_dir() or stage.is_symlink():
        raise TransactionError(f"staging directory missing or unsafe: {stage}")
    batch = stage / f"batch-r{round_number:02d}.jsonl"
    notes = stage / f"NOTES-r{round_number:02d}.md"
    if not batch.is_file() or batch.is_symlink():
        raise TransactionError(f"required staged batch missing or unsafe: {batch}")
    if not notes.is_file() or notes.is_symlink():
        raise TransactionError(f"required staged notes missing or unsafe: {notes}")
    if not notes.read_text().strip():
        raise TransactionError(f"staged notes are empty: {notes}")
    coverage_error = validate_novel_coverage(notes, factory_dir)
    if coverage_error:
        raise TransactionError(coverage_error)

    errors, warnings, kinds, records = check_jsonl(
        batch,
        batch.name,
        seen_ids=committed_ids(factory_dir),
        factory_staging=True,
    )
    if errors or warnings:
        details = [*(f"ERROR: {item}" for item in errors), *(f"WARNING: {item}" for item in warnings)]
        raise TransactionError("staged batch is not training-ready:\n" + "\n".join(details))
    if records != expected:
        raise TransactionError(
            f"staged batch has {records} records; reservation requires exactly {expected}"
        )
    expected_kind = AGENTIC_FACTORY_KINDS.get(factory_dir.name)
    if expected_kind and set(kinds) != {expected_kind}:
        raise TransactionError(
            f"{factory_dir.name} requires only {expected_kind!r} records; "
            f"staged kinds are {sorted(kinds)!r}"
        )
    envelope_errors = validate_agentic_envelope(batch, factory_dir, round_number)
    if envelope_errors:
        raise TransactionError(
            "staged batch violates the agentic factory envelope:\n"
            + "\n".join(f"ERROR: {error}" for error in envelope_errors)
        )

    files = []
    rr = f"{round_number:02d}"
    allowed_core = {batch.name, notes.name}
    artifact_re = re.compile(
        rf"^[A-Za-z0-9][A-Za-z0-9._-]*-r{re.escape(rr)}\.(?:md|json|txt)$"
    )
    for path in sorted(stage.iterdir()):
        if not path.is_file() or path.is_symlink():
            raise TransactionError(f"staging contains a non-regular file: {path}")
        if path.suffix == ".jsonl" and path != batch:
            raise TransactionError(
                f"staging may contain only the reserved JSONL batch: {path.name}"
            )
        if path.name not in allowed_core and not artifact_re.fullmatch(path.name):
            raise TransactionError(
                "auxiliary artifacts must be safe round-scoped .md/.json/.txt "
                f"files ending in -r{rr}: {path.name}"
            )
        files.append(
            {
                "name": path.name,
                "bytes": path.stat().st_size,
                "sha256": file_sha256(path),
            }
        )
    return files, kinds, records


def publish(factory_dir: Path, round_number: int, token: str):
    factory_dir = Path(factory_dir).resolve()
    with run_publish_lock(factory_dir):
        return _publish_locked(factory_dir, round_number, token)


def _publish_locked(factory_dir: Path, round_number: int, token: str):
    """Publish while holding the run-wide identity/commit lock."""
    paths = marker_paths(factory_dir, round_number)
    if paths["complete"].exists():
        raise TransactionError(f"round already complete: {paths['complete']}")
    reservation = read_json(paths["reservation"])
    if reservation.get("round") != round_number or reservation.get("token") != token:
        raise TransactionError("reservation round/token does not match publish request")
    stage = Path(reservation.get("staging_dir", "")).resolve()
    expected_stage = staging_dir(factory_dir, round_number, token).resolve()
    if stage != expected_stage:
        raise TransactionError(
            f"reservation staging path escaped its transaction root: {stage}"
        )
    expected = reservation.get("expected_records")
    if not isinstance(expected, int) or isinstance(expected, bool) or expected < 1:
        raise TransactionError("reservation has an invalid expected_records value")

    files, kinds, records = validate_stage(
        factory_dir,
        stage,
        round_number,
        expected,
    )
    manifest = {
        "version": 1,
        "factory": factory_dir.name,
        "round": round_number,
        "token": token,
        "expected_records": expected,
        "records": records,
        "kinds": kinds,
        "files": files,
        "published_at": utc_now(),
        "commit_point": paths["complete"].name,
    }

    resumed = paths["publishing"].exists()
    if resumed:
        existing = read_json(paths["publishing"])
        if existing != manifest:
            # Timestamps differ across retries. Compare the immutable plan.
            keys = ("factory", "round", "token", "expected_records", "records", "kinds", "files")
            if any(existing.get(key) != manifest.get(key) for key in keys):
                raise TransactionError(
                    f"publishing plan conflicts with staged content: {paths['publishing']}"
                )
        manifest = existing
    else:
        write_exclusive_json(paths["publishing"], manifest)

    for item in manifest["files"]:
        source = stage / item["name"]
        destination = factory_dir / item["name"]
        if destination.exists():
            if not resumed:
                raise TransactionError(f"refusing to replace existing output: {destination}")
            if not destination.is_file() or file_sha256(destination) != item["sha256"]:
                raise TransactionError(f"refusing to replace conflicting output: {destination}")
            continue
        try:
            os.link(source, destination, follow_symlinks=False)
        except FileExistsError:
            if not destination.is_file() or file_sha256(destination) != item["sha256"]:
                raise TransactionError(f"publication race at {destination}")

    # Linking this marker is the atomic visibility point for the whole round.
    try:
        os.link(paths["publishing"], paths["complete"], follow_symlinks=False)
    except FileExistsError as exc:
        raise TransactionError(f"completion marker already exists: {paths['complete']}") from exc

    paths["publishing"].unlink(missing_ok=True)
    paths["reservation"].unlink(missing_ok=True)
    shutil.rmtree(stage, ignore_errors=True)
    return manifest


def abort(factory_dir: Path, round_number: int, token: str):
    """Release an unpublished reservation so a failed round can be retried.

    Without this, a generation failure between reserve and publish leaves the
    reservation in place and `reserve` rejects the round forever, blocking the
    factory frontier. Refuses to touch a round that already started publishing
    or completed — those are past the commit point and must not be rolled back.
    """
    factory_dir = Path(factory_dir).resolve()
    paths = marker_paths(factory_dir, round_number)
    if paths["complete"].exists():
        raise TransactionError(
            f"round r{round_number:02d} is already committed; refusing to abort"
        )
    if paths["publishing"].exists():
        raise TransactionError(
            f"round r{round_number:02d} is mid-publish; resume publish instead of aborting"
        )
    if not paths["reservation"].exists():
        raise TransactionError(f"no reservation to abort for round r{round_number:02d}")
    reservation = read_json(paths["reservation"])
    if reservation.get("token") != token:
        raise TransactionError("reservation token mismatch")

    stage = Path(reservation.get("staging_dir", "")).resolve()
    expected_stage = staging_dir(factory_dir, round_number, token).resolve()
    if stage == expected_stage:
        shutil.rmtree(stage, ignore_errors=True)
    paths["reservation"].unlink(missing_ok=True)
    return {
        "factory": factory_dir.name,
        "round": round_number,
        "aborted": True,
        "released_staging_dir": str(stage),
        "next_round": frontier_status(factory_dir)["next_round"],
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    front = sub.add_parser("frontier")
    front.add_argument("factory_dir")
    res = sub.add_parser("reserve")
    res.add_argument("factory_dir")
    res.add_argument("--round", type=int, required=True, dest="round_number")
    res.add_argument("--expected", type=int, required=True)
    pub = sub.add_parser("publish")
    pub.add_argument("factory_dir")
    pub.add_argument("--round", type=int, required=True, dest="round_number")
    pub.add_argument("--token", required=True)
    abt = sub.add_parser("abort")
    abt.add_argument("factory_dir")
    abt.add_argument("--round", type=int, required=True, dest="round_number")
    abt.add_argument("--token", required=True)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        if args.command == "frontier":
            result = frontier_status(Path(args.factory_dir))
        elif args.command == "reserve":
            result = reserve(Path(args.factory_dir), args.round_number, args.expected)
        elif args.command == "abort":
            result = abort(Path(args.factory_dir), args.round_number, args.token)
        else:
            result = publish(Path(args.factory_dir), args.round_number, args.token)
    except (OSError, TransactionError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
