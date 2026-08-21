#!/usr/bin/env python3
"""Reserve, stage, validate, and atomically publish one factory round.

Generated data is written outside ``outputs/raw`` first.  A round becomes
visible to frontier readers only when ``ROUND-rNN.complete.json`` is linked
into the factory directory after every staged file has passed validation and
been copied without replacing an existing path.

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
import stat
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from check_records import check_jsonl  # noqa: E402
from validate_run import THALAMIC_CORE_KEYS  # noqa: E402


MODE_FILE = ".round-marker-mode.json"
BATCH_RE = re.compile(r"^batch-r(\d+)([a-z]*)\.jsonl$")
COMPLETE_RE = re.compile(r"^ROUND-r(\d+)\.complete\.json$")
PUBLISHING_RE = re.compile(r"^ROUND-r(\d+)\.publishing\.json$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
TOKEN_RE = re.compile(r"^[0-9a-f]{32}$")
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
RESTART_LANE_SCENARIO_TERMS = {
    "eval-harness-trajectory-factory": (
        ("eval", "deepeval", "pytest"),
        ("harness", "judge", "scorer", "fixture"),
        ("fail", "drift", "mismatch", "error"),
        ("repair", "fix", "correct"),
        ("verify", "valid", "pass"),
    ),
    "incident-response-oncall-factory": (
        ("incident", "on-call", "oncall", "outage"),
        ("root cause", "rca", "red herring"),
        ("mitigat", "rollback", "repair", "fix"),
        ("verify", "recover", "healthy", "resolved"),
    ),
    "data-pipeline-repair-factory": (
        ("pipeline", "etl", "data"),
        ("schema drift", "late data", "schema", "late"),
        ("repair", "backfill", "fix"),
        ("verify", "reconcile", "valid", "pass"),
    ),
    "git-ops-recovery-factory": (
        ("git", "rebase", "detached head", "ci"),
        ("conflict", "detached", "failure", "broken"),
        ("recover", "repair", "rebase", "fix"),
        ("verify", "clean", "pass", "commit"),
    ),
    "browser-tool-use-factory": (
        ("browser", "selector", "dom", "page"),
        ("selector fail", "stale", "not found", "timeout"),
        ("retry", "repair", "fallback", "fix"),
        ("verify", "loaded", "found", "pass"),
    ),
    "rag-retrieval-debug-factory": (
        ("rag", "retrieval", "chunk", "citation"),
        ("wrong chunk", "citation miss", "irrelevant", "missed"),
        ("rerank", "repair", "query", "fix"),
        ("verify", "ground", "relevant", "citation"),
    ),
    "code-review-preference-factory": (
        ("review", "patch", "diff"),
        ("bug", "defect", "risk", "incorrect"),
        ("prefer", "better", "reject", "critique"),
        ("verify", "test", "correct", "safe"),
    ),
    "infra-as-code-factory": (
        ("terraform", "kubernetes", "k8s", "infrastructure"),
        ("misconfig", "drift", "plan", "policy"),
        ("repair", "fix", "correct"),
        ("verify", "validate", "plan", "pass"),
    ),
    "api-contract-migration-factory": (
        ("openapi", "api", "contract"),
        ("drift", "breaking", "incompatib", "schema"),
        ("migrat", "repair", "compatib", "fix"),
        ("verify", "validate", "pass", "compatible"),
    ),
    "observability-debug-factory": (
        ("trace", "metric", "observability", "telemetry"),
        ("lie", "mislead", "incorrect", "mismatch"),
        ("diagnos", "repair", "fix", "correct"),
        ("verify", "correlat", "valid", "pass"),
    ),
    "package-release-factory": (
        ("package", "release", "artifact", "version"),
        ("manifest", "attestation", "provenance"),
        ("repair", "fix", "correct"),
        ("verify", "valid", "pass"),
    ),
    "flaky-test-quarantine-factory": (
        ("flaky", "nondeterministic", "intermittent"),
        ("trigger", "seed", "timing", "repro"),
        ("quarantine", "repair", "fix"),
        ("verify", "stable", "repeat", "pass"),
    ),
    "db-migration-repair-factory": (
        ("migration", "backfill", "schema"),
        ("ordering", "compatib", "rollback", "preflight"),
        ("repair", "fix", "additive"),
        ("post-migration", "verify", "check", "pass"),
    ),
    "sandbox-refusal-factory": (
        ("sandbox", "escape", "secret", "credential", "unsafe"),
        ("refus", "deny", "prohibit"),
        ("safe alternative", "redacted alternative", "bounded alternative"),
        ("policy", "blocked", "outcome"),
    ),
    "monorepo-dep-bump-factory": (
        ("workspace", "monorepo", "dependency"),
        ("lockfile", "peer", "build graph", "build-graph"),
        ("repair", "compatible", "pin", "bump"),
        ("verify", "build", "pass"),
    ),
    "mcp-tool-schema-drift-factory": (
        ("mcp", "tools/list", "tool schema"),
        ("mismatch", "incompatib", "field", "version"),
        ("request", "repair", "correct"),
        ("verify", "valid", "success"),
    ),
    "llm-eval-flakiness-factory": (
        ("judge", "rubric", "scorer", "seed"),
        ("flaky", "instability", "varying", "nondeterministic"),
        ("stabil", "pin", "aggregate"),
        ("verify", "stable", "repeat"),
    ),
    "k8s-crashloop-factory": (
        ("crashloop", "kubernetes", "k8s"),
        ("config", "probe", "image", "dependency", "logs", "status"),
        ("repair", "fix", "rollout"),
        ("verify", "recover", "ready", "criterion"),
    ),
    "proto-breaking-change-factory": (
        ("protobuf", "proto", "wire"),
        ("tag", "field", "semantic", "incompatib"),
        ("additive", "migration", "reserve"),
        ("verify", "compatible", "check"),
    ),
    "docker-build-cache-factory": (
        ("docker", "buildkit", "layer"),
        ("cache", "stale", "invalidation", "key"),
        ("rebuild", "repair", "no-cache"),
        ("verify", "artifact", "input"),
    ),
    "authz-regression-factory": (
        ("authorization", "authz", "idor", "bfla"),
        ("denied", "allowed", "boundary", "privilege"),
        ("repair", "policy", "fix"),
        ("verify", "test", "confirmed"),
    ),
    "agent-memory-compaction-factory": (
        ("memory", "compaction"),
        ("stale", "lost", "evict", "retain"),
        ("keep", "evict", "retained"),
        ("verify", "relevant", "task state"),
    ),
    "prompt-cache-invalidation-factory": (
        ("prompt", "cache", "prefix"),
        ("schema", "tool", "change", "key"),
        ("invalidate", "recompute"),
        ("verify", "fresh", "updated"),
    ),
    "notebook-to-pipeline-factory": (
        ("notebook", "pipeline"),
        ("schema", "input", "operational"),
        ("preserve", "reproducible", "transform"),
        ("verify", "output", "repeat"),
    ),
    "secret-scan-remediation-factory": (
        ("secret", "credential", "scan"),
        ("false-positive", "detected", "pattern"),
        ("redact", "rotate", "allowlist"),
        ("verify", "scan", "clean"),
    ),
    "cache-stampede-factory": (
        ("cache", "stampede", "miss"),
        ("concurrent", "contention", "overload"),
        ("singleflight", "lock", "backoff"),
        ("verify", "bounded", "load"),
    ),
    "distributed-lock-factory": (
        ("lease", "fencing", "split-brain", "lock"),
        ("expiry", "stale", "ownership", "token"),
        ("repair", "fence", "renew"),
        ("verify", "cannot commit", "reject"),
    ),
}
NOVEL_COVERAGE_RE = re.compile(
    r"^\s*novel[ _-]?coverage\s*(?:\([^)\n]*\))?\s*[:=]?\s*(\d+(?:\.\d+)?)\s*%",
    re.IGNORECASE | re.MULTILINE,
)
CASCADE_GENERIC_TERMS = frozenset(
    {
        "and",
        "are",
        "error",
        "errors",
        "failed",
        "failure",
        "fault",
        "for",
        "from",
        "has",
        "have",
        "into",
        "issue",
        "not",
        "problem",
        "step",
        "that",
        "the",
        "this",
        "was",
        "were",
        "with",
    }
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
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TransactionError(f"cannot read transaction file {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise TransactionError(f"transaction file must contain an object: {path}")
    return value


def marker_mode_path(factory_dir: Path) -> Path | None:
    """Return a safe marker-mode file, or ``None`` when marker mode is absent."""
    mode_path = factory_dir / MODE_FILE
    if not mode_path.exists() and not mode_path.is_symlink():
        return None
    if not mode_path.is_file() or mode_path.is_symlink():
        raise TransactionError(f"unsafe marker mode file: {mode_path}")
    return mode_path


def regular_file_metadata(path: Path):
    """Return size and digest from one no-follow regular-file descriptor."""
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise TransactionError(f"cannot open regular file safely {path}: {exc}") from exc
    try:
        metadata = os.fstat(fd)
        if not stat.S_ISREG(metadata.st_mode):
            raise TransactionError(f"unsafe non-regular file: {path}")
        digest = hashlib.sha256()
        with os.fdopen(fd, "rb") as handle:
            fd = -1
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return metadata.st_size, digest.hexdigest()
    finally:
        if fd >= 0:
            os.close(fd)


def file_sha256(path: Path):
    _size, digest = regular_file_metadata(path)
    return digest


def copy_verified_exclusive(source: Path, destination: Path, expected_sha256: str):
    """Atomically publish a verified copy without sharing the staged inode."""
    source_flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        source_flags |= os.O_NOFOLLOW
    try:
        source_fd = os.open(source, source_flags)
    except OSError as exc:
        raise TransactionError(f"cannot open staged file safely {source}: {exc}") from exc
    if not stat.S_ISREG(os.fstat(source_fd).st_mode):
        os.close(source_fd)
        raise TransactionError(f"staged source is not a regular file: {source}")
    temporary = destination.parent / f".{destination.name}.{uuid.uuid4().hex}.publishing"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = -1
    try:
        fd = os.open(temporary, flags, 0o644)
        with os.fdopen(source_fd, "rb") as input_handle, os.fdopen(fd, "wb") as output_handle:
            source_fd = -1
            fd = -1
            shutil.copyfileobj(input_handle, output_handle)
            output_handle.flush()
            os.fsync(output_handle.fileno())
        if file_sha256(temporary) != expected_sha256:
            raise TransactionError(f"staged file changed while publishing: {source}")
        try:
            os.link(temporary, destination, follow_symlinks=False)
        except FileExistsError:
            if (
                not destination.is_file()
                or destination.is_symlink()
                or file_sha256(destination) != expected_sha256
            ):
                raise TransactionError(f"publication race at {destination}")
    finally:
        if source_fd >= 0:
            os.close(source_fd)
        if fd >= 0:
            os.close(fd)
        temporary.unlink(missing_ok=True)


def valid_legacy_file(path: Path):
    """Return its record count when a legacy JSONL file fully deep-checks."""
    if not path.is_file() or path.is_symlink():
        return 0
    errors, _warnings, _kinds, records = check_jsonl(path, path.name)
    return 0 if errors else records


def validate_legacy_payload(
    path: Path, factory_dir: Path, round_number: int, seen_ids=None
):
    """Return a legacy payload's records and any applicable contract errors."""
    factory_staging = factory_dir.name in AGENTIC_FACTORY_KINDS
    errors, warnings, kinds, records = check_jsonl(
        path,
        path.name,
        seen_ids=seen_ids,
        factory_staging=factory_staging,
    )
    problems = list(errors)
    if factory_staging:
        problems.extend(warnings)
        expected_kind = AGENTIC_FACTORY_KINDS[factory_dir.name]
        if set(kinds) != {expected_kind}:
            problems.append(
                f"{factory_dir.name} requires only {expected_kind!r} records; "
                f"legacy kinds are {sorted(kinds)!r}"
            )
        if not errors:
            problems.extend(validate_agentic_envelope(path, factory_dir, round_number))
    return records, problems


def discover_legacy_frontier(factory_dir: Path):
    """Highest complete-looking legacy round, ignoring malformed name claims."""
    factory_dir = Path(factory_dir)
    quota = FACTORY_QUOTAS.get(factory_dir.name, 1)
    by_round: dict[int, int] = {}
    for path in factory_dir.glob("*.jsonl"):
        if not path.is_file() or path.is_symlink():
            continue
        match = BATCH_RE.fullmatch(path.name)
        if match:
            round_number = int(match.group(1))
        elif path.name in LEGACY_R1_NAMES:
            round_number = 1
        else:
            continue
        by_round[round_number] = by_round.get(round_number, 0) + valid_legacy_file(path)
    eligible = [round_number for round_number, count in by_round.items() if count >= quota]
    return max(eligible, default=0)


def discover_unmarked_legacy_frontier(factory_dir: Path):
    """Highest validated batch round not owned by a transaction marker."""
    factory_dir = Path(factory_dir)
    quota = FACTORY_QUOTAS.get(factory_dir.name, 1)
    by_round: dict[int, int] = {}
    for path in sorted(factory_dir.glob("batch-r*.jsonl")):
        if not path.is_file() or path.is_symlink():
            continue
        match = BATCH_RE.fullmatch(path.name)
        if match is None:
            continue
        round_number = int(match.group(1))
        markers = marker_paths(factory_dir, round_number)
        if any(
            marker.is_file() and not marker.is_symlink()
            for marker in (markers["publishing"], markers["complete"])
        ):
            continue
        records, problems = validate_legacy_payload(path, factory_dir, round_number)
        if not problems:
            by_round[round_number] = by_round.get(round_number, 0) + records
    eligible = [round_number for round_number, count in by_round.items() if count >= quota]
    return max(eligible, default=0)


def unowned_canonical_batch_collision(factory_dir: Path, round_number: int):
    """Return a next-round canonical path that no transaction marker owns."""
    path = factory_dir / f"batch-r{round_number:02d}.jsonl"
    if not path.exists() and not path.is_symlink():
        return None
    markers = marker_paths(factory_dir, round_number)
    if any(
        marker.is_file() and not marker.is_symlink()
        for marker in (markers["publishing"], markers["complete"])
    ):
        return None
    return path


def discover_legacy_named_baseline(factory_dir: Path):
    """Return the validated r01 floor contributed by pre-marker payload names."""
    factory_dir = Path(factory_dir)
    quota = FACTORY_QUOTAS.get(factory_dir.name, 1)
    has_transactional_r01 = any(
        path.is_file() and not path.is_symlink()
        for path in (
            factory_dir / "ROUND-r01.publishing.json",
            factory_dir / "ROUND-r01.complete.json",
        )
    )
    records = sum(
        valid_legacy_file(path)
        for path in factory_dir.glob("*.jsonl")
        if path.name in LEGACY_R1_NAMES
        or (
            not has_transactional_r01
            and (match := BATCH_RE.fullmatch(path.name)) is not None
            and int(match.group(1)) == 1
            and not match.group(2)
        )
    )
    return 1 if records >= quota else 0


def sibling_committed_and_inflight_ids(factory_dir: Path):
    """Seed a legacy handoff with IDs already owned by sibling factories."""
    factory_dir = Path(factory_dir)
    run_dir = factory_dir.parent
    seen_ids = {}
    for path in sorted(run_dir.glob("*.jsonl")):
        if path.is_file() and not path.is_symlink():
            check_jsonl(path, path.relative_to(run_dir), seen_ids=seen_ids)
    for sibling in sorted(run_dir.iterdir()):
        if sibling == factory_dir or not sibling.is_dir() or sibling.is_symlink():
            continue
        mode_path = marker_mode_path(sibling)
        if mode_path is None:
            paths = committed_jsonl_paths(sibling)
        else:
            mode = read_json(mode_path)
            baseline = mode.get("legacy_baseline")
            if (
                mode.get("version") != 1
                or mode.get("commit_point") != "ROUND-rNN.complete.json"
                or not isinstance(baseline, int)
                or isinstance(baseline, bool)
                or baseline < 0
            ):
                raise TransactionError(f"invalid sibling marker mode: {mode_path}")
            paths = legacy_baseline_jsonl_paths(sibling, baseline)
            for marker in sorted(sibling.glob("ROUND-r*.complete.json")):
                match = COMPLETE_RE.fullmatch(marker.name)
                if match is None or not marker.is_file() or marker.is_symlink():
                    continue
                round_number = int(match.group(1))
                payload = read_json(marker)
                if (
                    payload.get("factory") == sibling.name
                    and payload.get("round") == round_number
                    and payload.get("commit_point") == marker.name
                ):
                    batch = sibling / f"batch-r{round_number:02d}.jsonl"
                    if batch.is_file() and not batch.is_symlink():
                        paths.append(batch)
            paths.extend(in_flight_batch_paths(sibling))
        for path in sorted(set(paths)):
            try:
                label = path.relative_to(run_dir)
            except ValueError:
                label = Path(sibling.name) / ".inflight" / path.name
            check_jsonl(path, label, seen_ids=seen_ids)
    return seen_ids


def validate_legacy_baseline_payloads(factory_dir: Path, baseline: int):
    """Deep-check every regular legacy payload exposed by a marker baseline."""
    records_by_round = {}
    seen_ids = sibling_committed_and_inflight_ids(factory_dir)
    for path in sorted(factory_dir.glob("*.jsonl")):
        if not path.is_file() or path.is_symlink():
            continue
        match = BATCH_RE.fullmatch(path.name)
        if match is not None:
            round_number = int(match.group(1))
            if round_number > baseline:
                continue
        elif path.name in LEGACY_R1_NAMES and baseline >= 1:
            round_number = 1
        else:
            continue
        records, problems = validate_legacy_payload(
            path, factory_dir, round_number, seen_ids=seen_ids
        )
        if records < 1 or problems:
            details = "\n".join(f"ERROR: {problem}" for problem in problems)
            raise TransactionError(
                f"invalid legacy payload covered by marker baseline: {path}"
                + (f"\n{details}" if details else "")
            )
        records_by_round[round_number] = records_by_round.get(round_number, 0) + records
    quota = FACTORY_QUOTAS.get(factory_dir.name, 1)
    for round_number, records in records_by_round.items():
        if factory_dir.name in AGENTIC_FACTORY_KINDS and records != quota:
            raise TransactionError(
                f"legacy payloads for r{round_number:02d} require exactly {quota} "
                f"records for {factory_dir.name}; found {records}"
            )
        if records < quota:
            raise TransactionError(
                f"legacy payloads for r{round_number:02d} do not meet quota "
                f"{quota}: {factory_dir}"
            )
        if factory_dir.name in AGENTIC_FACTORY_KINDS:
            notes = factory_dir / f"NOTES-r{round_number:02d}.md"
            if not notes.is_file() or notes.is_symlink():
                raise TransactionError(
                    f"legacy baseline notes missing or unsafe for r{round_number:02d}: {notes}"
                )
            coverage_error = validate_novel_coverage(notes, factory_dir)
            if coverage_error:
                raise TransactionError(coverage_error)


def legacy_baseline_jsonl_paths(factory_dir: Path, baseline: int):
    """Return regular top-level JSONL made visible by a legacy baseline."""
    visible = []
    for path in sorted(factory_dir.glob("*.jsonl")):
        if not path.is_file() or path.is_symlink():
            continue
        match = BATCH_RE.fullmatch(path.name)
        if match is not None and int(match.group(1)) <= baseline:
            visible.append(path)
        elif baseline >= 1 and path.name in LEGACY_R1_NAMES:
            visible.append(path)
    return visible


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


def completed_manifests(factory_dir: Path) -> dict[int, dict]:
    """Return only completion manifests safe to use for batch visibility.

    ``completed_rounds`` intentionally remains a lightweight frontier-report
    helper for existing marker-mode directories.  Consumers that expose or
    reserve committed batch contents need the full transaction contract:
    a regular marker, its factory/round identity, its declared commit point,
    and matching regular, hashed files for every artifact it declares.
    """
    seen_ids = sibling_committed_and_inflight_ids(factory_dir)
    mode_path = marker_mode_path(factory_dir)
    if mode_path is not None:
        baseline = validated_marker_mode(factory_dir, mode_path)["legacy_baseline"]
        for legacy_path in legacy_baseline_jsonl_paths(factory_dir, baseline):
            errors, _warnings, _kinds, _records = check_jsonl(
                legacy_path,
                legacy_path.name,
                seen_ids=seen_ids,
            )
            if errors:
                raise TransactionError(
                    f"legacy baseline ID validation failed: {legacy_path}\n"
                    + "\n".join(f"ERROR: {error}" for error in errors)
                )
    manifests = {}
    for path in sorted(factory_dir.glob("ROUND-r*.complete.json")):
        match = COMPLETE_RE.fullmatch(path.name)
        if match is None:
            continue
        if not path.is_file() or path.is_symlink():
            raise TransactionError(f"unsafe completion marker: {path}")
        round_number = int(match.group(1))
        payload = read_json(path)
        if payload.get("factory") != factory_dir.name:
            raise TransactionError(f"completion marker identity mismatch: {path}")
        declared_round = payload.get("round")
        if (
            not isinstance(declared_round, int)
            or isinstance(declared_round, bool)
            or declared_round != round_number
        ):
            raise TransactionError(f"completion marker round mismatch: {path}")
        if payload.get("commit_point") != path.name:
            raise TransactionError(f"completion marker commit point mismatch: {path}")
        files = payload.get("files")
        if not isinstance(files, list):
            raise TransactionError(f"completion marker files must be an array: {path}")
        batch_name = f"batch-r{round_number:02d}.jsonl"
        notes_name = f"NOTES-r{round_number:02d}.md"
        names = set()
        for entry in files:
            name = entry.get("name") if isinstance(entry, dict) else None
            digest = entry.get("sha256") if isinstance(entry, dict) else None
            if (
                not isinstance(name, str)
                or not name
                or Path(name).name != name
                or name in names
            ):
                raise TransactionError(f"completion marker has an unsafe file entry: {path}")
            if not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None:
                raise TransactionError(f"completion marker has invalid file hash: {path}")
            names.add(name)
            completion_manifest_file_matches(factory_dir / name, payload)
        if batch_name not in names:
            raise TransactionError(
                f"completion marker has no unique batch entry: {path}"
            )
        if notes_name not in names:
            raise TransactionError(
                f"completion marker has no unique notes entry: {path}"
            )
        coverage_error = validate_novel_coverage(factory_dir / notes_name, factory_dir)
        if coverage_error:
            raise TransactionError(coverage_error)
        validate_completed_batch(
            factory_dir, round_number, payload, seen_ids=seen_ids
        )
        # The semantic validators reopen the committed artifacts.  Recheck
        # every manifest-bound byte afterwards so content swapped during
        # validation cannot advance the visible frontier.
        for name in names:
            completion_manifest_file_matches(factory_dir / name, payload)
        if round_number in manifests:
            raise TransactionError(f"duplicate completion markers for r{round_number:02d}")
        manifests[round_number] = payload
    return manifests


def completion_manifest_file_matches(path: Path, manifest: dict) -> bool:
    """Validate one regular committed artifact against its manifest entry."""
    if not path.is_file() or path.is_symlink():
        raise TransactionError(f"unsafe committed artifact: {path}")
    entries = [
        entry
        for entry in manifest["files"]
        if isinstance(entry, dict) and entry.get("name") == path.name
    ]
    if len(entries) != 1:
        raise TransactionError(f"completion marker has no unique file entry for {path}")
    digest = entries[0].get("sha256")
    if not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None:
        raise TransactionError(f"completion marker has invalid file hash for {path}")
    if file_sha256(path) != digest:
        raise TransactionError(f"completed file hash mismatch: {path}")
    return True


def batch_matches_completion_manifest(batch: Path, manifest: dict) -> bool:
    """Validate a committed batch against its unique completion entry."""
    completion_manifest_file_matches(batch, manifest)
    return True


def nested_key_paths(value, key, path=""):
    """Yield every nested occurrence of one forbidden field name."""
    if isinstance(value, dict):
        for child_key, item in value.items():
            child_path = f"{path}.{child_key}" if path else child_key
            if child_key == key:
                yield child_path
            yield from nested_key_paths(item, key, child_path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from nested_key_paths(item, key, f"{path}[{index}]")


def nested_strings(value):
    """Yield observable string values from a JSON-compatible value."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from nested_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from nested_strings(item)


def agentic_observable_text(record: dict) -> str:
    """Return lower-cased task and trajectory evidence, excluding metadata."""
    values = [
        record.get("goal"),
        record.get("steps"),
        record.get("outcome"),
        record.get("chosen"),
        record.get("rejected"),
        record.get("critique"),
    ]
    return " ".join(
        text.strip().casefold()
        for value in values
        for text in nested_strings(value)
        if text.strip()
    )


def long_horizon_scenario_signature(record: dict):
    """Return a stable codebase/bug-class signature, falling back to the goal."""
    meta = record.get("meta")
    meta = meta if isinstance(meta, dict) else {}

    def normalized_field(*values):
        for value in values:
            if isinstance(value, str) and value.strip():
                return re.sub(r"\s+", " ", value.strip().casefold())
        return None

    codebase = normalized_field(
        record.get("codebase_type"),
        record.get("codebase"),
        record.get("repository"),
        meta.get("codebase_type"),
        meta.get("codebase"),
        meta.get("repository"),
    )
    bug_class = normalized_field(
        record.get("bug_class"),
        meta.get("bug_class"),
    )
    if codebase is not None and bug_class is not None:
        return ("explicit", codebase, bug_class)
    goal = normalized_field(record.get("goal"))
    return ("goal", goal) if goal is not None else None


def banned_agentic_wrapper_paths(value, path=""):
    """Yield nested fields or values that introduce neuromorphic wrappers."""
    if isinstance(value, dict):
        for key, item in value.items():
            child_path = f"{path}.{key}" if path else key
            normalized = str(key).casefold()
            if (
                normalized in {"spike_events", "raster", "rasters"}
                or normalized.endswith("_raster")
                or "spikenaut" in normalized
                or "neuromorphic" in normalized
            ):
                yield child_path
            yield from banned_agentic_wrapper_paths(item, child_path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from banned_agentic_wrapper_paths(item, f"{path}[{index}]")
    elif isinstance(value, str):
        normalized = value.casefold()
        if "spikenaut" in normalized or "neuromorphic" in normalized:
            yield path or "<root>"


def shares_visible_terms(left, right):
    """Whether two observable strings name at least one meaningful common term."""
    if not isinstance(left, str) or not isinstance(right, str):
        return False
    left_terms = {
        term
        for term in re.findall(r"[a-z0-9][a-z0-9_-]{2,}", left.lower())
        if term not in CASCADE_GENERIC_TERMS
    }
    right_terms = {
        term
        for term in re.findall(r"[a-z0-9][a-z0-9_-]{2,}", right.lower())
        if term not in CASCADE_GENERIC_TERMS
    }
    return bool(left_terms & right_terms)


def numbered_horizon_errors(where, steps, lane, minimum, maximum):
    """Return lane-specific horizon and exact integer numbering errors."""
    if not isinstance(steps, list):
        return []
    errors = []
    if not minimum <= len(steps) <= maximum:
        errors.append(f"{where}: {lane} episodes require {minimum} to {maximum} steps")
    errors.extend(contiguous_step_number_errors(where, steps, lane))
    return errors


def contiguous_step_number_errors(where, steps, lane):
    """Return an error unless list entries use exact integer numbering 1..K."""
    if not isinstance(steps, list):
        return []
    step_numbers = [
        step.get("n") if isinstance(step, dict) else None
        for step in steps
    ]
    if any(
        not isinstance(number, int)
        or isinstance(number, bool)
        or number != expected_number
        for expected_number, number in enumerate(step_numbers, 1)
    ):
        return [f"{where}: {lane} steps must be numbered contiguously from 1"]
    return []


def observable_step_text(step):
    """Flatten only publishable tool/basis/observation fields for lane checks."""
    if not isinstance(step, dict):
        return ""
    values = [step.get("decision_basis"), step.get("observation")]
    tool_call = step.get("tool_call")
    if isinstance(tool_call, dict):
        values.extend((tool_call.get("name"), tool_call.get("args")))
    return " ".join(
        value if isinstance(value, str) else json.dumps(value, sort_keys=True)
        for value in values
        if isinstance(value, (str, dict, list))
    ).lower()


def has_long_horizon_debug_loop(steps):
    """Whether observable steps contain edit, failing test, re-read, fix, verify."""
    if not isinstance(steps, list):
        return False
    texts = [observable_step_text(step) for step in steps]

    def includes(text, terms):
        return any(term in text for term in terms)

    edit_terms = ("edit", "write", "patch", "apply")
    test_terms = ("test", "pytest", "cargo test", "npm test")
    failure_terms = ("fail", "error", "nonzero", "red")
    read_terms = ("re-read", "reread", "inspect", "read", "cat ", "sed ", "rg ")
    fix_terms = ("fix", "repair", "patch", "edit", "write", "apply")
    verify_terms = ("pass", "success", "green", "verified", "fixed")
    for edit_index, text in enumerate(texts):
        if not includes(text, edit_terms):
            continue
        for failure_index in range(edit_index + 1, len(texts)):
            failure_text = texts[failure_index]
            if not (
                includes(failure_text, test_terms)
                and includes(failure_text, failure_terms)
            ):
                continue
            for read_index in range(failure_index + 1, len(texts)):
                if not includes(texts[read_index], read_terms):
                    continue
                for fix_index in range(read_index + 1, len(texts)):
                    if not includes(texts[fix_index], fix_terms):
                        continue
                    return any(
                        includes(texts[verify_index], test_terms)
                        and includes(texts[verify_index], verify_terms)
                        for verify_index in range(fix_index + 1, len(texts))
                    )
    return False


def abandoned_failed_hypotheses(steps):
    """Return distinct explicit hypothesis labels failed then abandoned later."""
    if not isinstance(steps, list):
        return set()
    failed = []
    failure_terms = ("fail", "disproved", "ruled out", "not the cause")
    for index, step in enumerate(steps):
        observation = step.get("observation") if isinstance(step, dict) else None
        if not isinstance(observation, str) or not any(
            term in observation.lower() for term in failure_terms
        ):
            continue
        failed.extend(
            (index, match.group(1))
            for match in re.finditer(
                r"\bhypothesis\s*[:#_-]?\s*([a-z0-9][a-z0-9_-]{2,})",
                observation.lower(),
            )
        )
    abandoned = set()
    abandonment_terms = ("abandon", "discard", "reject", "disproved", "ruled out")
    for failure_index, label in failed:
        for step in steps[failure_index + 1 :]:
            basis = step.get("decision_basis") if isinstance(step, dict) else None
            if (
                isinstance(basis, str)
                and label in basis.lower()
                and any(term in basis.lower() for term in abandonment_terms)
            ):
                abandoned.add(label)
                break
    return abandoned


def frontier_status(factory_dir: Path):
    factory_dir = Path(factory_dir).resolve()
    if not factory_dir.is_dir():
        raise TransactionError(f"not a factory directory: {factory_dir}")
    mode_path = marker_mode_path(factory_dir)
    if mode_path is None:
        baseline = discover_legacy_frontier(factory_dir)
        return {
            "factory": factory_dir.name,
            "mode": "legacy",
            "baseline": baseline,
            "completed_markers": [],
            "highest_flushed": baseline,
            "next_round": baseline + 1,
        }

    mode = validated_marker_mode(factory_dir, mode_path)
    baseline = mode["legacy_baseline"]
    # The next reservable round must use the same validated commit contract as
    # batch visibility. A matching integer alone must not advance a lane.
    markers = sorted(completed_manifests(factory_dir))
    highest = baseline
    marker_set = set(markers)
    while highest + 1 in marker_set:
        highest += 1
    noncontiguous = [number for number in markers if number > highest]
    collision = unowned_canonical_batch_collision(factory_dir, highest + 1)
    if collision is not None:
        raise TransactionError(
            f"unowned canonical batch collision at next round: {collision}"
        )
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
    existing = marker_mode_path(factory_dir)
    if existing is not None:
        return validated_marker_mode(factory_dir, existing)
    baseline = discover_legacy_frontier(factory_dir)
    validate_legacy_baseline_payloads(factory_dir, baseline)
    payload = {
        "version": 1,
        "created_at": utc_now(),
        "legacy_baseline": baseline,
        "commit_point": "ROUND-rNN.complete.json",
    }
    try:
        write_exclusive_json(mode_path, payload)
        return payload
    except FileExistsError:
        existing = marker_mode_path(factory_dir)
        if existing is None:
            raise TransactionError(f"marker mode disappeared while creating it: {mode_path}")
        return validated_marker_mode(factory_dir, existing)


def validated_marker_mode(factory_dir: Path, mode_path: Path | None = None):
    """Read a marker-mode declaration only when its legacy handoff is real."""
    if mode_path is None:
        mode_path = marker_mode_path(factory_dir)
    if mode_path is None:
        raise TransactionError(f"marker mode is not enabled for {factory_dir}")
    mode = read_json(mode_path)
    if mode.get("version") != 1:
        raise TransactionError(f"unsupported marker mode version in {mode_path}")
    if mode.get("commit_point") != "ROUND-rNN.complete.json":
        raise TransactionError(f"invalid marker mode commit point in {mode_path}")
    baseline = mode.get("legacy_baseline")
    if not isinstance(baseline, int) or isinstance(baseline, bool) or baseline < 0:
        raise TransactionError(f"invalid legacy_baseline in {mode_path}")
    legacy_frontier = discover_legacy_frontier(factory_dir)
    if baseline > legacy_frontier:
        raise TransactionError(
            f"legacy_baseline in {mode_path} exceeds discovered legacy frontier "
            f"r{legacy_frontier:02d}"
        )
    legacy_named_baseline = discover_legacy_named_baseline(factory_dir)
    if baseline < legacy_named_baseline:
        raise TransactionError(
            f"legacy_baseline in {mode_path} excludes validated legacy r01 payloads"
        )
    unmarked_frontier = discover_unmarked_legacy_frontier(factory_dir)
    if baseline < unmarked_frontier:
        raise TransactionError(
            f"legacy_baseline in {mode_path} excludes validated unmarked legacy "
            f"frontier r{unmarked_frontier:02d}"
        )
    validate_legacy_baseline_payloads(factory_dir, baseline)
    return mode


def staging_dir(factory_dir: Path, round_number: int, token: str):
    """Return the private transaction stage for one validated reservation token."""
    if not isinstance(token, str) or TOKEN_RE.fullmatch(token) is None:
        raise TransactionError("reservation token must be 32 lowercase hexadecimal characters")
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


def validated_reservation_stage(
    factory_dir: Path, round_number: int, token: str, stage_text
):
    """Return the lexical reserved stage after rejecting symlinked components."""
    expected = staging_dir(factory_dir, round_number, token)
    if not isinstance(stage_text, str) or Path(stage_text) != expected:
        raise TransactionError(
            f"reservation staging path escaped its transaction root: {stage_text!r}"
        )
    stage_root = expected.parents[2]
    current = stage_root
    for part in (None, *expected.relative_to(stage_root).parts):
        if part is not None:
            current /= part
        if current.is_symlink():
            raise TransactionError(f"reservation staging directory is unsafe: {current}")
    return expected


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
    mode_path = marker_mode_path(factory_dir)
    if mode_path is None:
        return sorted(
            path
            for path in factory_dir.rglob("*.jsonl")
            if path.is_file() and not path.is_symlink()
        )

    files = sorted(
        path
        for path in factory_dir.glob("*.jsonl")
        if path.is_file() and not path.is_symlink()
    )

    mode = validated_marker_mode(factory_dir, mode_path)
    baseline = mode["legacy_baseline"]
    manifests = completed_manifests(factory_dir)
    visible = []
    for path in files:
        match = BATCH_RE.fullmatch(path.name)
        if match is not None:
            round_number = int(match.group(1))
            suffix = match.group(2)
            if round_number <= baseline:
                visible.append(path)
            elif not suffix and round_number in manifests and batch_matches_completion_manifest(
                path, manifests[round_number]
            ):
                visible.append(path)
            continue
        if baseline >= 1 and path.name in LEGACY_R1_NAMES:
            visible.append(path)
    return visible


def in_flight_batch_paths(factory_dir: Path):
    """Yield batches protected by an unfinished publishing marker.

    A publishing marker means the transaction has already passed the global ID
    scan. Its IDs must remain reserved to other factory publishers even if the
    batch has linked before the completion marker. The caller's own factory is
    deliberately excluded by ``committed_ids`` so an interrupted transaction
    can validate and resume its identical staged batch.
    """
    for marker in sorted(factory_dir.glob("ROUND-r*.publishing.json")):
        match = PUBLISHING_RE.fullmatch(marker.name)
        if match is None:
            continue
        round_number = int(match.group(1))
        manifest = read_json(marker)
        if manifest.get("factory") != factory_dir.name or manifest.get("round") != round_number:
            raise TransactionError(f"publishing marker identity mismatch: {marker}")
        reservation_path = marker_paths(factory_dir, round_number)["reservation"]
        if not reservation_path.is_file():
            raise TransactionError(f"publishing marker has no reservation: {marker}")
        reservation = read_json(reservation_path)
        token = reservation.get("token")
        if not isinstance(token, str) or token != manifest.get("token"):
            raise TransactionError(f"publishing marker token mismatch: {marker}")
        try:
            stage = validated_reservation_stage(
                factory_dir, round_number, token, reservation.get("staging_dir")
            )
        except TransactionError as exc:
            raise TransactionError(
                f"publishing marker staging path is unsafe: {marker}: {exc}"
            ) from exc
        batch_name = f"batch-r{round_number:02d}.jsonl"
        staged_batch = stage / batch_name
        if staged_batch.is_file() and not staged_batch.is_symlink():
            yield staged_batch
            continue
        linked_batch = factory_dir / batch_name
        if linked_batch.is_file() and not linked_batch.is_symlink():
            yield linked_batch
            continue
        raise TransactionError(f"publishing marker has no readable batch: {marker}")


def committed_ids(factory_dir: Path):
    """Seed the run-wide ID namespace from committed/legacy raw JSONL."""
    seen_ids = {}
    run_dir = factory_dir.parent
    for path in sorted(run_dir.glob("*.jsonl")):
        # Dated runs may retain pre-factory legacy JSONL at their root. It
        # remains part of the run-wide namespace even though it has no
        # factory marker directory of its own.
        if path.is_file():
            check_jsonl(path, path.relative_to(run_dir), seen_ids=seen_ids)
    for candidate in sorted(run_dir.iterdir()):
        if not candidate.is_dir():
            continue
        for path in committed_jsonl_paths(candidate):
            # Existing defects are reported by run audits. Here we only need
            # their identity namespace so a new round cannot reuse it.
            check_jsonl(path, path.relative_to(run_dir), seen_ids=seen_ids)
        if candidate != factory_dir:
            for path in in_flight_batch_paths(candidate):
                # Staging sits alongside ``raw``, so this path is not always
                # relative to the run directory.  Its label is diagnostic
                # only; the path itself remains the source for ID checking.
                label = Path(candidate.name) / ".inflight" / path.name
                check_jsonl(path, label, seen_ids=seen_ids)
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
    safety_case_types = []
    cascade_fault_kinds = []
    cascade_recovery_values = []
    long_horizon_success_values = []
    long_horizon_scenario_signatures = []
    tool_use_lesson_signatures = []
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
        if factory_dir.name == "safety-calibration-factory" and isinstance(record, dict):
            safety_case_types.append(record.get("case_type"))
        for path in sorted(set(banned_agentic_wrapper_paths(record))):
            errors.append(
                f"{where}: agentic records must not include spike_events, Spikenaut, "
                f"or neuromorphic rasters at {path}"
            )
        scenario_terms = RESTART_LANE_SCENARIO_TERMS.get(factory_dir.name)
        if scenario_terms is not None and isinstance(record, dict):
            visible_text = agentic_observable_text(record)
            if any(
                not any(term in visible_text for term in alternatives)
                for alternatives in scenario_terms
            ):
                errors.append(
                    f"{where}: {factory_dir.name} must demonstrate its required "
                    "failure scenario, bounded correction, and observable verification"
                )
        if factory_dir.name == "cascading-error-recovery-factory":
            fault = record.get("error_introduced") if isinstance(record, dict) else None
            steps = record.get("steps") if isinstance(record, dict) else None
            diagnosis = record.get("diagnosis") if isinstance(record, dict) else None
            reward = record.get("reward") if isinstance(record, dict) else None
            errors.extend(
                contiguous_step_number_errors(where, steps, "cascading-error recovery")
            )
            if not isinstance(fault, dict):
                errors.append(f"{where}: error_introduced must be an object")
            else:
                step_number = fault.get("step")
                if (
                    not isinstance(step_number, int)
                    or isinstance(step_number, bool)
                    or step_number < 2
                    or not isinstance(steps, list)
                    or step_number >= len(steps)
                ):
                    errors.append(
                        f"{where}: error_introduced.step must name a non-final step at least 2"
                    )
                if not isinstance(fault.get("kind"), str) or not fault["kind"].strip():
                    errors.append(f"{where}: error_introduced.kind must be a non-empty string")
                else:
                    cascade_fault_kinds.append(fault["kind"].strip().casefold())
                if not isinstance(fault.get("payload"), str) or not fault["payload"].strip():
                    errors.append(f"{where}: error_introduced.payload must be a non-empty string")
            if not isinstance(diagnosis, str) or not diagnosis.strip():
                errors.append(f"{where}: diagnosis must be a non-empty string")
            cascade_steps = reward.get("cascade_steps") if isinstance(reward, dict) else None
            recovered = reward.get("recovered") if isinstance(reward, dict) else None
            if (
                not isinstance(recovered, int)
                or isinstance(recovered, bool)
                or recovered not in (0, 1)
            ):
                errors.append(f"{where}: reward.recovered must be 0 or 1")
            else:
                cascade_recovery_values.append(recovered)
                success = reward.get("success") if isinstance(reward, dict) else None
                if isinstance(success, bool) and success != bool(recovered):
                    errors.append(
                        f"{where}: reward.success must agree with reward.recovered"
                    )
            if (
                not isinstance(cascade_steps, int)
                or isinstance(cascade_steps, bool)
                or not 3 <= cascade_steps <= 8
            ):
                errors.append(f"{where}: reward.cascade_steps must be an integer from 3 to 8")
            elif (
                isinstance(fault, dict)
                and isinstance(fault.get("step"), int)
                and not isinstance(fault.get("step"), bool)
                and isinstance(steps, list)
                and isinstance(diagnosis, str)
                and diagnosis.strip()
            ):
                fault_step = fault["step"]
                diagnosis_index = fault_step + cascade_steps
                recovery_index = diagnosis_index + 1
                fault_text = f"{fault.get('kind', '')} {fault.get('payload', '')}"
                if recovery_index >= len(steps):
                    errors.append(
                        f"{where}: cascade needs {cascade_steps} inherited steps, then diagnosis and recovery"
                    )
                else:
                    inherited = steps[fault_step:diagnosis_index]
                    if any(
                        not isinstance(step, dict)
                        or not shares_visible_terms(step.get("observation"), fault_text)
                        for step in inherited
                    ):
                        errors.append(
                            f"{where}: each inherited cascade step must visibly reference the fault"
                        )
                    diagnosis_step = steps[diagnosis_index]
                    diagnosis_text = " ".join(
                        value
                        for value in (
                            diagnosis_step.get("observation"),
                            diagnosis_step.get("reflection"),
                        )
                        if isinstance(value, str)
                    ) if isinstance(diagnosis_step, dict) else None
                    if not shares_visible_terms(diagnosis_text, fault_text):
                        errors.append(
                            f"{where}: diagnosis step must visibly name the fault"
                        )
                    recovery_step = steps[recovery_index]
                    recovery_basis = (
                        recovery_step.get("decision_basis")
                        if isinstance(recovery_step, dict)
                        else None
                    )
                    if not shares_visible_terms(recovery_basis, diagnosis):
                        errors.append(
                            f"{where}: recovery decision_basis must cite the diagnosis"
                        )
        if factory_dir.name == "long-horizon-coding-factory" and isinstance(record, dict):
            scenario_signature = long_horizon_scenario_signature(record)
            if scenario_signature is not None:
                long_horizon_scenario_signatures.append(scenario_signature)
            steps = record.get("steps")
            errors.extend(
                numbered_horizon_errors(
                    where,
                    steps,
                    "long-horizon coding",
                    18,
                    28,
                )
            )
            if not has_long_horizon_debug_loop(steps):
                errors.append(
                    f"{where}: long-horizon episodes require an observable edit, "
                    "failing test, re-read, fix, and passing verification loop"
                )
            reward = record.get("reward")
            success = reward.get("success") if isinstance(reward, dict) else None
            if isinstance(success, bool):
                long_horizon_success_values.append(success)
                outcome = record.get("outcome")
                outcome_text = outcome.casefold() if isinstance(outcome, str) else ""
                completion_evidence = re.search(
                    r"\b(?:passed|verified|fixed|repaired|landed|completed|succeeded)\b",
                    outcome_text,
                )
                partial_evidence = re.search(
                    r"\b(?:partial(?:ly)?|mitigat\w*|contain\w*|handoff|handed off|blocked|unresolved)\b",
                    outcome_text,
                )
                contradictory_completion = re.search(
                    r"\b(?:fully|fixed|repaired|landed|completed|succeeded)\b|all tests passed",
                    outcome_text,
                )
                if success and (completion_evidence is None or partial_evidence is not None):
                    errors.append(
                        f"{where}: successful long-horizon outcome must report "
                        "observable verification without partial or handoff language"
                    )
                if not success and (
                    partial_evidence is None or contradictory_completion is not None
                ):
                    errors.append(
                        f"{where}: unsuccessful long-horizon outcome must report "
                        "partial containment, mitigation, or handoff"
                    )
        if factory_dir.name == "multi-agent-coordination-factory" and isinstance(record, dict):
            transcript = record.get("transcript")
            disagreements = record.get("disagreements")
            resolution = record.get("resolution")
            if isinstance(transcript, list):
                if not 6 <= len(transcript) <= 16:
                    errors.append(
                        f"{where}: coordination transcripts require 6 to 16 turns"
                    )
                turn_contents = [
                    turn.get("content") if isinstance(turn, dict) else None
                    for turn in transcript
                ]
                grounded = False
                if isinstance(disagreements, list) and isinstance(resolution, str):
                    for disagreement in disagreements:
                        disagreement_turns = [
                            index
                            for index, content in enumerate(turn_contents)
                            if shares_visible_terms(disagreement, content)
                        ]
                        resolution_turns = [
                            index
                            for index, content in enumerate(turn_contents)
                            if shares_visible_terms(resolution, content)
                        ]
                        if any(
                            disagreement_index < resolution_index
                            for disagreement_index in disagreement_turns
                            for resolution_index in resolution_turns
                        ) and shares_visible_terms(disagreement, resolution):
                            grounded = True
                            break
                if not grounded:
                    errors.append(
                        f"{where}: resolution must cite a disagreement grounded earlier in the transcript"
                    )
        if factory_dir.name == "sparse-reward-long-task-factory" and isinstance(record, dict):
            steps = record.get("steps")
            reward = record.get("reward")
            if isinstance(steps, list):
                errors.extend(
                    numbered_horizon_errors(
                        where,
                        steps,
                        "sparse long-task",
                        25,
                        60,
                    )
                )
                for index, step in enumerate(steps):
                    if isinstance(step, dict):
                        for field in ("reward", "score", "tests_passed"):
                            for path in nested_key_paths(step, field):
                                if field == "reward":
                                    errors.append(
                                        f"{where}: sparse long-task steps[{index}] "
                                        f"must not carry reward at {path}"
                                    )
                                else:
                                    errors.append(
                                        f"{where}: sparse long-task steps[{index}] "
                                        f"must not carry intermediate {field} at {path}"
                                    )
                horizon_steps = reward.get("horizon_steps") if isinstance(reward, dict) else None
                if (
                    not isinstance(horizon_steps, int)
                    or isinstance(horizon_steps, bool)
                    or horizon_steps != len(steps)
                ):
                    errors.append(
                        f"{where}: reward.horizon_steps must equal the staged step count"
                    )
                if len(abandoned_failed_hypotheses(steps)) < 2:
                    errors.append(
                        f"{where}: sparse long-task episodes require at least two "
                        "explicit hypotheses whose failure observations precede abandonment"
                    )
            if not isinstance(reward, dict) or reward.get("terminal_only") is not True:
                errors.append(f"{where}: reward.terminal_only must be true")
        if AGENTIC_FACTORY_KINDS[factory_dir.name] == "preference":
            if (
                factory_dir.name == "tool-use-preference-factory"
                and isinstance(record, dict)
            ):
                chosen = record.get("chosen")
                rejected = record.get("rejected")
                lesson = {
                    "goal": record.get("goal"),
                    "critique": record.get("critique"),
                    "chosen": {
                        key: chosen.get(key) if isinstance(chosen, dict) else None
                        for key in ("goal", "steps", "outcome", "reward")
                    },
                    "rejected": {
                        key: rejected.get(key) if isinstance(rejected, dict) else None
                        for key in ("goal", "steps", "outcome", "reward")
                    },
                }
                tool_use_lesson_signatures.append(
                    json.dumps(lesson, sort_keys=True, separators=(",", ":"))
                )
            for side_name in ("chosen", "rejected"):
                side = record.get(side_name) if isinstance(record, dict) else None
                if not isinstance(side, dict) or not isinstance(side.get("steps"), list):
                    errors.append(
                        f"{where}: {side_name} must be an episode side with steps"
                    )
                elif all(key in side for key in THALAMIC_CORE_KEYS):
                    errors.append(
                        f"{where}: {side_name} must not wrap a Thalamic trajectory"
                    )
                if (
                    factory_dir.name == "tool-use-preference-factory"
                    and isinstance(side, dict)
                ):
                    errors.extend(
                        numbered_horizon_errors(
                            where,
                            side.get("steps"),
                            f"tool-use preference {side_name}",
                            4,
                            10,
                        )
                    )
                side_reward = side.get("reward") if isinstance(side, dict) else None
                success = side_reward.get("success") if isinstance(side_reward, dict) else None
                required_success = side_name == "chosen"
                if isinstance(success, bool) and success is not required_success:
                    errors.append(
                        f"{where}: {side_name}.reward.success must be "
                        f"{str(required_success).lower()}"
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
    if factory_dir.name == "safety-calibration-factory":
        required_case_types = {
            "correct_refusal",
            "incorrect_refusal",
            "missed_refusal",
        }
        if len(safety_case_types) != len(required_case_types) or set(safety_case_types) != required_case_types:
            errors.append(
                "safety-calibration-factory requires exactly one each of "
                "correct_refusal, incorrect_refusal, and missed_refusal per batch"
            )
    if factory_dir.name == "cascading-error-recovery-factory" and sorted(
        cascade_recovery_values
    ) != [0, 1]:
        errors.append(
            "cascading-error-recovery-factory requires one full recovery and "
            "one partial containment or handoff per batch"
        )
    if (
        factory_dir.name == "cascading-error-recovery-factory"
        and len(cascade_fault_kinds) == 2
        and len(set(cascade_fault_kinds)) != 2
    ):
        errors.append(
            "cascading-error-recovery-factory requires two distinct "
            "error_introduced.kind fault classes per batch"
        )
    if factory_dir.name == "long-horizon-coding-factory" and sorted(
        long_horizon_success_values
    ) != [False, True]:
        errors.append(
            "long-horizon-coding-factory requires one success and one partial "
            "containment, mitigation, or handoff per batch"
        )
    if (
        factory_dir.name == "long-horizon-coding-factory"
        and len(long_horizon_scenario_signatures) == 2
        and len(set(long_horizon_scenario_signatures)) != 2
    ):
        errors.append(
            "long-horizon-coding-factory requires two distinct codebase and "
            "bug-class scenarios per batch"
        )
    if (
        factory_dir.name == "tool-use-preference-factory"
        and len(tool_use_lesson_signatures) != len(set(tool_use_lesson_signatures))
    ):
        errors.append(
            "tool-use-preference-factory requires three distinct tool-use lessons per batch"
        )
    return errors


def validate_completed_batch(
    factory_dir: Path, round_number: int, manifest: dict, seen_ids=None
):
    """Re-run publication record, quota, and envelope checks for one marker."""
    batch = factory_dir / f"batch-r{round_number:02d}.jsonl"
    factory_staging = factory_dir.name in AGENTIC_FACTORY_KINDS
    errors, warnings, kinds, records = check_jsonl(
        batch,
        batch.name,
        seen_ids=seen_ids,
        factory_staging=factory_staging,
    )
    if errors or warnings:
        details = [
            *(f"ERROR: {item}" for item in errors),
            *(f"WARNING: {item}" for item in warnings),
        ]
        raise TransactionError(
            f"committed batch is not training-ready: {batch}\n" + "\n".join(details)
        )
    for field in ("records", "expected_records"):
        if field not in manifest or (
            not isinstance(manifest[field], int)
            or isinstance(manifest[field], bool)
            or manifest[field] != records
        ):
            raise TransactionError(
                f"completion marker {field} does not match batch records: {batch}"
            )
    if "kinds" in manifest and manifest["kinds"] != kinds:
        raise TransactionError(f"completion marker kinds do not match batch: {batch}")
    if manifest.get("version") != 1:
        raise TransactionError(f"unsupported completion marker version for {batch}")
    if factory_staging:
        expected_kind = AGENTIC_FACTORY_KINDS[factory_dir.name]
        if set(kinds) != {expected_kind}:
            raise TransactionError(
                f"{factory_dir.name} requires only {expected_kind!r} records; "
                f"committed kinds are {sorted(kinds)!r}"
            )
        quota = FACTORY_QUOTAS[factory_dir.name]
        if records != quota:
            raise TransactionError(
                f"committed batch has {records} records; {factory_dir.name} "
                f"requires exactly {quota}: {batch}"
            )
        envelope_errors = validate_agentic_envelope(batch, factory_dir, round_number)
        if envelope_errors:
            raise TransactionError(
                f"committed batch violates the agentic factory envelope: {batch}\n"
                + "\n".join(f"ERROR: {error}" for error in envelope_errors)
            )


def validate_novel_coverage(notes: Path, factory_dir: Path, notes_text: str | None = None):
    """Require a usable Novel coverage percentage for fixed agentic lanes."""
    if factory_dir.name not in AGENTIC_FACTORY_KINDS:
        return None
    if notes_text is None:
        try:
            notes_text = notes.read_text()
        except (OSError, UnicodeError) as exc:
            return f"cannot read notes as UTF-8: {notes}: {exc}"
    match = NOVEL_COVERAGE_RE.search(notes_text)
    if match is None:
        return f"notes need a 'Novel coverage: <N>%' line: {notes}"
    value = float(match.group(1))
    if not 0 <= value <= 100:
        return f"Novel coverage must be between 0% and 100%: {notes}"
    return None


def validate_stage(
    factory_dir: Path,
    stage: Path,
    round_number: int,
    expected: int,
):
    if not stage.is_dir() or stage.is_symlink():
        raise TransactionError(f"staging directory missing or unsafe: {stage}")
    try:
        initial_paths = sorted(stage.iterdir())
    except OSError as exc:
        raise TransactionError(f"cannot inspect staging directory {stage}: {exc}") from exc
    initial_files = {}
    for path in initial_paths:
        if not path.is_file() or path.is_symlink():
            raise TransactionError(f"staging contains a non-regular file: {path}")
        initial_files[path.name] = regular_file_metadata(path)
    batch = stage / f"batch-r{round_number:02d}.jsonl"
    notes = stage / f"NOTES-r{round_number:02d}.md"
    if not batch.is_file() or batch.is_symlink():
        raise TransactionError(f"required staged batch missing or unsafe: {batch}")
    if not notes.is_file() or notes.is_symlink():
        raise TransactionError(f"required staged notes missing or unsafe: {notes}")
    try:
        notes_text = notes.read_text()
    except (OSError, UnicodeError) as exc:
        raise TransactionError(f"cannot read staged notes as UTF-8: {notes}: {exc}") from exc
    if not notes_text.strip():
        raise TransactionError(f"staged notes are empty: {notes}")
    coverage_error = validate_novel_coverage(notes, factory_dir, notes_text)
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
    final_names = set()
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
        metadata = regular_file_metadata(path)
        if initial_files.get(path.name) != metadata:
            raise TransactionError(f"staged file changed during validation: {path}")
        final_names.add(path.name)
        files.append(
            {
                "name": path.name,
                "bytes": metadata[0],
                "sha256": metadata[1],
            }
        )
    if final_names != set(initial_files):
        raise TransactionError("staging file set changed during validation")
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
    stage = validated_reservation_stage(
        factory_dir, round_number, token, reservation.get("staging_dir")
    )
    expected = reservation.get("expected_records")
    if not isinstance(expected, int) or isinstance(expected, bool) or expected < 1:
        raise TransactionError("reservation has an invalid expected_records value")
    configured_quota = FACTORY_QUOTAS.get(factory_dir.name)
    if factory_dir.name in AGENTIC_FACTORY_KINDS and expected != configured_quota:
        raise TransactionError(
            f"reservation for {factory_dir.name} requires exactly "
            f"{configured_quota} records; found {expected}"
        )

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
        # Timestamps differ across retries. Every other field is immutable,
        # including the schema version and declared completion marker.
        existing_plan = {
            key: value for key, value in existing.items() if key != "published_at"
        }
        manifest_plan = {
            key: value for key, value in manifest.items() if key != "published_at"
        }
        if existing_plan != manifest_plan:
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
            if (
                not destination.is_file()
                or destination.is_symlink()
                or file_sha256(destination) != item["sha256"]
            ):
                raise TransactionError(f"refusing to replace conflicting output: {destination}")
            continue
        copy_verified_exclusive(source, destination, item["sha256"])

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
    with run_publish_lock(factory_dir):
        return _abort_locked(factory_dir, round_number, token)


def _abort_locked(factory_dir: Path, round_number: int, token: str):
    """Abort only when no publisher owns this run's transaction lock."""
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

    stage = validated_reservation_stage(
        factory_dir, round_number, token, reservation.get("staging_dir")
    )
    if stage.is_symlink() or (stage.exists() and not stage.is_dir()):
        raise TransactionError(f"reservation staging directory is unsafe: {stage}")
    if stage.exists():
        shutil.rmtree(stage)
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
