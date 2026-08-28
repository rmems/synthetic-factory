#!/usr/bin/env python3
"""Integration and promotion gate for the curation pass (bead ``sf-c5l.7``).

The six curation lanes each write their own curated JSONL tree plus a
record-level manifest. This module is the seventh, final step: it composes
those lane outputs into **one brand-new cleaned destination**, runs every
structural and corpus-level gate on that destination, records a stratified
human-review sample, and promotes to a **brand-new curated path** only when
``training_ready`` is true and the sample has been reviewed.

Composition order and evidence
------------------------------

The order is data, not code: it lives in an integration plan (``--plan``) so a
reviewer can read the exact chain that produced a corpus. Every lane must pair
its output tree with a record-level manifest. The gate authenticates each
emitted record and its exact source bytes against that manifest, then composes
lanes by stable source identity. Each lane output is a three-way delta from the
immutable source: changes at disjoint JSON paths survive together, while two
different changes to the same path fail closed. Terminal exclusion and
quarantine decisions suppress that source record. Unrelated records in the
same JSONL path survive, and every composition is recorded in the manifest.

The documented order for run ``2026-08-17`` is::

    1. sf-c5l.1  bridge_event_time_order   (timing repair / quarantine)
    2. sf-c5l.2  curate_identity           (canonical IDs + provenance)
    3. sf-c5l.3  preference_purity         (same-context pairs)
    4. sf-c5l.4  reward_ontology           (comparability classes)
    5. sf-c5l.5  coding_observability      (no hidden chain-of-thought)
    6. sf-c5l.6  tag_taxonomy              (controlled vocabulary)

Plan schema (``curation-integration-plan/v1``)::

    {
      "schema": "curation-integration-plan/v1",
      "source_run": "outputs/raw/2026-08-17",
      "lanes": [
        {
          "bead": "sf-c5l.1",
          "transform": "bridge_event_time_order",
          "version": "1.0.0",
          "outputs": "lane-bridge",              # dir of curated *.jsonl
          "manifest": "lane-bridge/manifest.jsonl"  # required, record-level
        }
      ]
    }

The reward lane also declares its ``reward_source_sidecars`` artifact. A
lane that used ``--units-migration`` additionally declares the copied
``reward_units_migration`` artifact so calibration claims can be rederived
from the sealed catalog. A
production ``source_run`` beginning with ``outputs/raw`` resolves from the
repository root, so the example remains valid when the plan lives under
``outputs/curation``. A short value such as ``raw`` remains plan-relative for
isolated fixtures. Relative ``outputs``/``manifest``/artifact paths always
resolve against the plan file's directory. Authenticated manifests and reward
sidecars are copied into the cleaned tree as governance evidence and verified
again before promotion.

Usage
-----

::

    python3 pipelines/curate_gate.py integrate \\
        --plan outputs/curation/plan.json \\
        --cleaned-out outputs/cleaned/2026-08-17-curated-v1

    # a human fills in verdicts for every sampled record, then:
    python3 pipelines/curate_gate.py promote \\
        --cleaned outputs/cleaned/2026-08-17-curated-v1 \\
        --review review-verdicts.json \\
        --curated-out outputs/curated/2026-08-17-v1

Both subcommands refuse to write into a destination that already exists, and
neither ever writes into ``outputs/raw/``.
"""

from __future__ import annotations

import argparse
import copy
import ctypes
import errno
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Sequence

_PIPELINES = Path(__file__).resolve().parent
_REPO = _PIPELINES.parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import curate_rewards  # noqa: E402
import curate_identity  # noqa: E402
import training_audit  # noqa: E402
from check_records import canonical_record_id, reject_json_constant  # noqa: E402
from validate_run import check_line  # noqa: E402

TOOL_NAME = "curate_gate"
TOOL_VERSION = "1.0.0"

PLAN_SCHEMA = "curation-integration-plan/v1"
MANIFEST_SCHEMA = "curation-manifest/v1"
SAMPLE_SCHEMA = "curation-review-sample/v1"
REVIEW_SCHEMA = "curation-review-verdicts/v1"

MANIFEST_FILENAME = "curation-manifest.json"
SAMPLE_FILENAME = "review-sample.json"
REVIEW_FILENAME = "review-verdicts.json"
GOVERNANCE_DIRNAME = "governance"
LANE_MANIFEST_DIRNAME = "lane-manifests"
REWARD_SIDECAR_DIRNAME = "reward-sidecars"
REWARD_CALIBRATION_DIRNAME = "reward-calibrations"

REWARD_SIDECAR_KIND = "reward_source_sidecars"
REWARD_CALIBRATION_KIND = "reward_units_migration"
REWARD_ARTIFACT_KINDS = frozenset({REWARD_SIDECAR_KIND, REWARD_CALIBRATION_KIND})
SHA256_HEX_RE = re.compile(r"^(?:sha256:)?([0-9a-f]{64})$")

VALIDATOR = _PIPELINES / "validate_run.py"
CHECKER = _PIPELINES / "check_records.py"

DEFAULT_PER_STRATUM = 2

RAW_OUTPUT_ROOT = (_REPO / "outputs" / "raw").resolve()

# The integration gate is meaningful only after every upstream lane has run.
# Bead IDs fix the dependency order; transform names bind each position to the
# reviewed implementation contract rather than accepting an arbitrary subset.
REQUIRED_LANES = (
    ("sf-c5l.1", "bridge_event_time_order"),
    ("sf-c5l.2", "curate_identity"),
    ("sf-c5l.3", "same-context-preference-curation"),
    ("sf-c5l.4", "reward_ontology"),
    ("sf-c5l.5", "coding_observability"),
    ("sf-c5l.6", "tag_taxonomy"),
)

# Which Thalamic view speaks for a record when stratifying by safety gate.
DECISION_ROLE_PRIORITY = ("record", "chosen", "language_view.trajectory", "rejected")

EXCLUSION_ACTIONS = frozenset({"excluded", "exclude", "dropped", "drop"})
QUARANTINE_ACTIONS = frozenset({"quarantine", "quarantined"})
RETAIN_ACTIONS = frozenset({"retained", "retain", "unchanged"})
REPAIR_ACTIONS = frozenset(
    {"changed", "flagged", "migrated", "modified", "modify", "repair", "repaired", "transformed"}
)
NO_OUTPUT_ACTIONS = EXCLUSION_ACTIONS | QUARANTINE_ACTIONS | frozenset({"skipped", "skip"})
OUTPUT_ACTIONS = RETAIN_ACTIONS | REPAIR_ACTIONS
KNOWN_ACTIONS = OUTPUT_ACTIONS | NO_OUTPUT_ACTIONS
DERIVED_CHANGE_REASON = "INTEGRATION_OUTPUT_DIFFERS_FROM_SOURCE"

ACCEPT_VERDICTS = frozenset({"accept", "accepted", "pass"})
REJECT_VERDICTS = frozenset({"reject", "rejected", "fail", "block"})

MANIFEST_LIST_KEYS = ("decisions", "manifest", "entries", "records", "items")


class GateError(Exception):
    """Operator-facing failure: bad plan, bad input, or an unsafe destination."""


# ---------------------------------------------------------------------------
# hashing helpers
# ---------------------------------------------------------------------------


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_regular_file_snapshot(path: Path, label: str) -> tuple[bytes, str, int]:
    """Capture one regular file once and bind its bytes to its pathname identity."""
    path = Path(path)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise GateError(f"cannot open {label} {path} without following links: {exc}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise GateError(f"{label} is not a regular file: {path}")
        if before.st_nlink != 1:
            raise GateError(f"{label} is multiply linked: {path}")
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 1 << 20):
            chunks.append(chunk)
        payload = b"".join(chunks)
        after_descriptor = os.fstat(descriptor)
        try:
            after_path = path.lstat()
        except OSError as exc:
            raise GateError(f"{label} changed while it was being read: {path}") from exc
        identity_before = (
            before.st_dev,
            before.st_ino,
            before.st_mode,
            before.st_nlink,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        )
        identity_after_descriptor = (
            after_descriptor.st_dev,
            after_descriptor.st_ino,
            after_descriptor.st_mode,
            after_descriptor.st_nlink,
            after_descriptor.st_size,
            after_descriptor.st_mtime_ns,
            after_descriptor.st_ctime_ns,
        )
        identity_after_path = (
            after_path.st_dev,
            after_path.st_ino,
            after_path.st_mode,
            after_path.st_nlink,
            after_path.st_size,
            after_path.st_mtime_ns,
            after_path.st_ctime_ns,
        )
        if (
            identity_after_descriptor != identity_before
            or identity_after_path != identity_before
            or len(payload) != before.st_size
        ):
            raise GateError(f"{label} changed while it was being read: {path}")
        return payload, sha256_hex(payload), len(payload)
    finally:
        os.close(descriptor)


def _tree_snapshot(root: Path) -> list[dict[str, Any]]:
    """Hash one staging tree and reject aliases or mid-read replacements."""
    root = Path(root)
    entries: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).parts):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise GateError(f"staging tree contains a symlink: {path}")
        before = path.lstat()
        if stat.S_ISDIR(before.st_mode):
            entries.append({"path": relative, "kind": "directory"})
            continue
        if not stat.S_ISREG(before.st_mode):
            raise GateError(f"staging tree contains a non-regular file: {path}")
        if before.st_nlink != 1:
            raise GateError(f"staging tree contains a multiply linked file: {path}")
        digest = file_sha256(path)
        after = path.lstat()
        identity_before = (
            before.st_dev,
            before.st_ino,
            before.st_mode,
            before.st_nlink,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        )
        identity_after = (
            after.st_dev,
            after.st_ino,
            after.st_mode,
            after.st_nlink,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        )
        if identity_after != identity_before:
            raise GateError(f"staging file changed while it was being hashed: {path}")
        entries.append(
            {
                "path": relative,
                "kind": "file",
                "sha256": digest,
                "bytes": after.st_size,
            }
        )
    return entries


def _lf_lines(text: str) -> list[str]:
    """Split JSONL only at LF; U+2028/U+2029 are valid JSON string data."""
    return text.split("\n")


def _all_jsonl_paths(root: Path) -> list[Path]:
    return sorted(root.rglob("*.jsonl"), key=lambda path: path.relative_to(root).parts)


def jsonl_paths(root: Path) -> list[Path]:
    """Corpus ``*.jsonl`` files, excluding copied governance evidence."""
    return [
        path
        for path in _all_jsonl_paths(root)
        if path.relative_to(root).parts[0] != GOVERNANCE_DIRNAME
    ]


def count_records(path: Path) -> int:
    text = path.read_text(encoding="utf-8", errors="replace")
    return sum(1 for line in _lf_lines(text) if line.strip())


def corpus_digest(root: Path) -> str:
    """Digest of the JSONL corpus only, so sidecar reports do not disturb it."""
    digest = hashlib.sha256()
    for path in jsonl_paths(root):
        rel = path.relative_to(root).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_sha256(path).encode("ascii"))
        digest.update(b"\n")
    return f"sha256:{digest.hexdigest()}"


def record_sha256(value: Any) -> str:
    try:
        blob = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise GateError(f"record is not canonical JSON data: {exc}") from exc
    return sha256_hex(blob.encode("utf-8"))


def _normalized_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise GateError(f"{label} must be a SHA-256")
    match = SHA256_HEX_RE.fullmatch(value)
    if match is None:
        raise GateError(f"{label} must be a SHA-256")
    return match.group(1)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def _load_json(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise GateError(f"cannot read {path}: {exc}") from exc
    try:
        return json.loads(text, parse_constant=reject_json_constant)
    except (json.JSONDecodeError, ValueError) as exc:
        raise GateError(f"{path}: invalid JSON: {exc}") from exc


def _resolve_declared_path(base: Path, value: str, label: str) -> Path:
    """Resolve one plan-relative path without erasing symlink evidence."""
    declared = Path(value)
    if declared.is_absolute() or ".." in declared.parts:
        raise GateError(f"{label} must stay within the plan directory: {value!r}")

    walked = base
    for part in declared.parts:
        if part in {"", "."}:
            continue
        walked = walked / part
        if walked.is_symlink():
            raise GateError(f"{label} contains a symlinked path component: {walked}")

    resolved = (base / declared).resolve()
    if resolved != base and base not in resolved.parents:
        raise GateError(f"{label} resolves outside the plan directory: {resolved}")
    return resolved


def _resolve_source_run_path(plan_dir: Path, value: str, label: str) -> Path:
    """Resolve a source tree without making the documented raw path ambiguous."""
    declared = Path(value)
    if declared.is_absolute() or ".." in declared.parts:
        raise GateError(
            f"{label} must be plan-relative or repository-relative beneath outputs/raw: {value!r}"
        )

    parts = tuple(part for part in declared.parts if part not in {"", "."})
    if not parts:
        raise GateError(f"{label} must name a directory")

    repository_raw = len(parts) >= 2 and parts[:2] == ("outputs", "raw")
    root = _REPO if repository_raw else plan_dir
    walked = root
    for part in parts:
        walked = walked / part
        if walked.is_symlink():
            raise GateError(f"{label} contains a symlinked path component: {walked}")

    resolved = (root / Path(*parts)).resolve()
    allowed_root = RAW_OUTPUT_ROOT if repository_raw else plan_dir
    if resolved != allowed_root and allowed_root not in resolved.parents:
        scope = "outputs/raw" if repository_raw else "the plan directory"
        raise GateError(f"{label} resolves outside {scope}: {resolved}")
    return resolved


def _lane_manifest_format(path: Path, label: str) -> str:
    """Return the only two evidence formats understood by promotion."""
    if path.suffix == ".json":
        return "json"
    if path.suffix == ".jsonl":
        return "jsonl"
    raise GateError(f"{label} must end in .json or .jsonl: {path}")


def _relative_artifact_destination(value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise GateError(f"{label} must be a non-empty relative path")
    destination = Path(value)
    if destination.is_absolute() or ".." in destination.parts:
        raise GateError(f"{label} must stay within its governance directory: {value!r}")
    parts = tuple(part for part in destination.parts if part not in {"", "."})
    if not parts:
        raise GateError(f"{label} must name a file")
    return Path(*parts)


# ---------------------------------------------------------------------------
# integration plan
# ---------------------------------------------------------------------------


def load_plan(plan_path: Path) -> dict[str, Any]:
    """Read and validate an integration plan; resolve its lane paths."""
    plan_path = Path(plan_path).resolve()
    payload, plan_sha256, _plan_size = _read_regular_file_snapshot(
        plan_path, "integration plan"
    )
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GateError(f"{plan_path}: integration plan is not UTF-8: {exc}") from exc
    try:
        plan = json.loads(text, parse_constant=reject_json_constant)
    except (json.JSONDecodeError, ValueError) as exc:
        raise GateError(f"{plan_path}: invalid JSON: {exc}") from exc
    if not isinstance(plan, dict):
        raise GateError(f"{plan_path}: plan must be a JSON object")
    schema = plan.get("schema")
    if schema is not None and schema != PLAN_SCHEMA:
        raise GateError(f"{plan_path}: unsupported plan schema {schema!r}")
    source_run = plan.get("source_run")
    if not isinstance(source_run, str) or not source_run.strip():
        raise GateError(f"{plan_path}: plan needs a non-empty string 'source_run'")

    base = plan_path.parent
    source_run_dir = _resolve_source_run_path(base, source_run, f"{plan_path}: source_run")
    if not source_run_dir.is_dir():
        raise GateError(f"{plan_path}: source_run directory is missing: {source_run_dir}")

    lanes = plan.get("lanes")
    if not isinstance(lanes, list) or not lanes:
        raise GateError(f"{plan_path}: plan needs a non-empty 'lanes' list")

    resolved: list[dict[str, Any]] = []
    versions: dict[str, str] = {}
    seen_outputs: dict[Path, str] = {}
    for index, lane in enumerate(lanes, 1):
        if not isinstance(lane, dict):
            raise GateError(f"{plan_path}: lane {index} must be an object")
        transform = lane.get("transform")
        version = lane.get("version")
        outputs = lane.get("outputs")
        for field, value in (("transform", transform), ("version", version), ("outputs", outputs)):
            if not isinstance(value, str) or not value.strip():
                raise GateError(f"{plan_path}: lane {index} needs a non-empty string '{field}'")
        previous = versions.get(transform)
        if previous is not None and previous != version:
            raise GateError(
                f"{plan_path}: transform {transform!r} declared at two versions "
                f"({previous!r} and {version!r})"
            )
        versions[transform] = version

        outputs_path = _resolve_declared_path(
            base, outputs, f"{plan_path}: lane {index} ({transform}) outputs"
        )
        if not outputs_path.is_dir():
            raise GateError(
                f"{plan_path}: lane {index} ({transform}) outputs directory is missing: "
                f"{outputs_path}"
            )
        if outputs_path in seen_outputs:
            raise GateError(
                f"{plan_path}: lane {index} ({transform}) reuses the outputs directory of "
                f"lane {seen_outputs[outputs_path]}: {outputs_path}"
            )
        seen_outputs[outputs_path] = f"{index} ({transform})"

        manifest = lane.get("manifest")
        if not isinstance(manifest, str) or not manifest.strip():
            raise GateError(
                f"{plan_path}: lane {index} ({transform}) needs a non-empty string 'manifest'"
            )
        manifest_path = _resolve_declared_path(
            base, manifest, f"{plan_path}: lane {index} ({transform}) manifest"
        )
        if not manifest_path.is_file():
            raise GateError(
                f"{plan_path}: lane {index} ({transform}) manifest is missing: {manifest_path}"
            )
        manifest_format = _lane_manifest_format(
            manifest_path,
            f"{plan_path}: lane {index} ({transform}) manifest",
        )

        raw_artifacts = lane.get("artifacts", [])
        if not isinstance(raw_artifacts, list):
            raise GateError(f"{plan_path}: lane {index} ({transform}) artifacts must be a list")
        artifacts: list[dict[str, Any]] = []
        destinations: set[Path] = set()
        for artifact_index, artifact in enumerate(raw_artifacts, 1):
            label = f"{plan_path}: lane {index} ({transform}) artifact {artifact_index}"
            if not isinstance(artifact, dict):
                raise GateError(f"{label} must be an object")
            kind = artifact.get("kind")
            if kind not in REWARD_ARTIFACT_KINDS:
                raise GateError(f"{label} has unsupported kind {kind!r}")
            value = artifact.get("path")
            if not isinstance(value, str) or not value.strip():
                raise GateError(f"{label} path must be a non-empty string")
            artifact_path = _resolve_declared_path(base, value, f"{label} path")
            if not artifact_path.is_file():
                raise GateError(f"{label} is missing: {artifact_path}")
            if artifact_path == manifest_path:
                raise GateError(f"{label} cannot reuse the lane manifest")
            destination_name = artifact.get("destination", artifact_path.name)
            destination = _relative_artifact_destination(destination_name, f"{label} destination")
            if destination in destinations:
                raise GateError(f"{label} reuses artifact destination {destination}")
            destinations.add(destination)
            artifacts.append(
                {
                    "kind": kind,
                    "source_path": artifact_path,
                    "destination": destination,
                }
            )

        resolved.append(
            {
                "order": index,
                "bead": lane.get("bead"),
                "transform": transform,
                "version": version,
                "outputs_dir": outputs_path,
                "manifest_path": manifest_path,
                "manifest_format": manifest_format,
                "artifacts": artifacts,
            }
        )

    declared_lanes = tuple((lane["bead"], lane["transform"]) for lane in resolved)
    if declared_lanes != REQUIRED_LANES:
        expected = ", ".join(f"{bead}:{transform}" for bead, transform in REQUIRED_LANES)
        actual = ", ".join(f"{bead}:{transform}" for bead, transform in declared_lanes)
        raise GateError(
            f"{plan_path}: lanes must be the six required contracts in order; "
            f"expected [{expected}], got [{actual}]"
        )

    reward_lane = next(lane for lane in resolved if lane["transform"] == "reward_ontology")
    if not reward_lane["artifacts"]:
        raise GateError(
            f"{plan_path}: reward_ontology must declare at least one "
            f"{REWARD_SIDECAR_KIND!r} artifact"
        )

    return {
        "plan_path": plan_path,
        "plan_sha256": plan_sha256,
        "source_run": source_run,
        "source_run_dir": source_run_dir,
        "lanes": resolved,
        "transform_versions": dict(sorted(versions.items())),
    }


# ---------------------------------------------------------------------------
# composition
# ---------------------------------------------------------------------------


def _assert_new_destination(destination: Path, label: str) -> Path:
    declared = Path(os.path.abspath(destination))
    if os.path.lexists(declared):
        raise GateError(f"refusing to overwrite an existing {label}: {declared}")
    resolved = declared.resolve(strict=False)
    if resolved == RAW_OUTPUT_ROOT or RAW_OUTPUT_ROOT in resolved.parents:
        raise GateError(f"refusing to write {label} beneath immutable raw output: {declared}")
    return resolved


def _rename_noreplace(
    source: Path,
    destination: Path,
    label: str,
    expected_tree: Sequence[dict[str, Any]],
) -> None:
    """Atomically publish one directory while refusing an existing pathname."""
    source = Path(source)
    destination = Path(destination)
    if _tree_snapshot(source) != list(expected_tree):
        raise GateError(f"{label} staging tree changed after final validation")
    if os.name == "nt":
        try:
            source.rename(destination)
        except FileExistsError as exc:
            raise GateError(f"refusing to overwrite an existing {label}: {destination}") from exc
        except OSError as exc:
            raise GateError(f"cannot publish {label} {destination}: {exc}") from exc
        return

    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise GateError("atomic no-replace publication is unavailable on this platform")
    renameat2.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    renameat2.restype = ctypes.c_int
    at_fdcwd = -100
    rename_noreplace = 1
    result = renameat2(
        at_fdcwd,
        os.fsencode(source),
        at_fdcwd,
        os.fsencode(destination),
        rename_noreplace,
    )
    if result == 0:
        return
    error = ctypes.get_errno()
    if error in {errno.EEXIST, errno.ENOTEMPTY}:
        raise GateError(f"refusing to overwrite an existing {label}: {destination}")
    raise GateError(f"cannot atomically publish {label} {destination}: {os.strerror(error)}")


def _logical_source_path(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GateError(f"{label} must be a non-empty source path")
    path = Path(value)
    parts = path.parts
    raw_roots = [
        index for index in range(len(parts) - 1) if parts[index : index + 2] == ("outputs", "raw")
    ]
    if raw_roots:
        raw_index = raw_roots[-1] + 1
        if len(parts) <= raw_index + 2:
            raise GateError(f"{label} does not identify a record below outputs/raw")
        parts = parts[raw_index + 2 :]
    elif path.is_absolute():
        raise GateError(f"{label} must be relative or identify a path below outputs/raw")
    parts = tuple(part for part in parts if part not in {"", "."})
    if not parts or ".." in parts:
        raise GateError(f"{label} is not a safe logical source path: {value!r}")
    return Path(*parts).as_posix()


def _assert_no_symlink(root: Path, path: Path, label: str) -> None:
    walked = root
    for part in path.relative_to(root).parts:
        walked = walked / part
        if walked.is_symlink():
            raise GateError(f"{label} contains a symlinked path: {walked}")


def _load_source_records(source_run: Path) -> dict[tuple[str, int], dict[str, Any]]:
    """Load the immutable source bytes used as the three-way merge base."""
    records: dict[tuple[str, int], dict[str, Any]] = {}
    paths = _all_jsonl_paths(source_run)
    if not paths:
        raise GateError(f"source_run holds no *.jsonl: {source_run}")
    for path in paths:
        _assert_no_symlink(source_run, path, "source_run")
        relative = path.relative_to(source_run).as_posix()
        payload, _payload_sha256, _payload_bytes = _read_regular_file_snapshot(
            path,
            "source JSONL",
        )
        for line_number, terminated in enumerate(payload.split(b"\n"), 1):
            raw_line = terminated[:-1] if terminated.endswith(b"\r") else terminated
            if not raw_line.strip():
                continue
            record: Any = None
            parse_error: str | None = None
            try:
                text = raw_line.decode("utf-8")
                record = json.loads(text, parse_constant=reject_json_constant)
            except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
                parse_error = str(exc)
            records[(relative, line_number)] = {
                "record": record,
                "source_hash": sha256_hex(raw_line),
                "parse_error": parse_error,
            }
    return records


_MISSING = object()


def _same_json(left: Any, right: Any) -> bool:
    if left is _MISSING or right is _MISSING:
        return left is right
    return type(left) is type(right) and left == right


def _json_pointer(parts: Sequence[str | int]) -> str:
    if not parts:
        return "/"
    tokens = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "/" + "/".join(tokens)


def _merge_lane_delta(
    baseline: Any,
    current: Any,
    lane_value: Any,
    *,
    source_key: tuple[str, int],
    transform: str,
    path: tuple[str | int, ...] = (),
) -> Any:
    """Apply one independently produced lane delta to the composed record.

    A lane may omit earlier lanes' changes because its output was derived from
    the immutable source record. Changes at disjoint JSON paths compose. The
    gate fails closed when two lanes make incompatible changes at one path.
    """
    if _same_json(lane_value, baseline):
        return copy.deepcopy(current)
    if _same_json(current, baseline):
        return _MISSING if lane_value is _MISSING else copy.deepcopy(lane_value)
    if _same_json(current, lane_value):
        return copy.deepcopy(current)

    if all(isinstance(value, dict) for value in (baseline, current, lane_value)):
        merged = copy.deepcopy(current)
        for key in sorted(set(baseline) | set(lane_value)):
            base_child = baseline.get(key, _MISSING)
            lane_child = lane_value.get(key, _MISSING)
            if _same_json(base_child, lane_child):
                continue
            current_child = current.get(key, _MISSING)
            result = _merge_lane_delta(
                base_child,
                current_child,
                lane_child,
                source_key=source_key,
                transform=transform,
                path=(*path, key),
            )
            if result is _MISSING:
                merged.pop(key, None)
            else:
                merged[key] = result
        return merged

    if all(isinstance(value, list) for value in (baseline, current, lane_value)) and (
        len(baseline) == len(current) == len(lane_value)
    ):
        return [
            _merge_lane_delta(
                base_child,
                current[index],
                lane_value[index],
                source_key=source_key,
                transform=transform,
                path=(*path, index),
            )
            for index, base_child in enumerate(baseline)
        ]

    source_path, source_line = source_key
    raise GateError(
        f"lane {transform!r} conflicts with an earlier lane at "
        f"{source_path}:{source_line}{_json_pointer(path)}"
    )


def _prepare_lane(
    lane: dict[str, Any], source_records: dict[tuple[str, int], dict[str, Any]]
) -> dict[str, Any]:
    """Authenticate one lane's emitted records against its declared manifest."""
    manifest_path = lane["manifest_path"]
    manifest_payload, manifest_sha256, manifest_bytes = _read_regular_file_snapshot(
        manifest_path,
        f"lane {lane['order']} ({lane['transform']}) manifest",
    )
    entries: list[dict[str, Any]] = []
    expected_by_path_hash: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    seen_sources: set[tuple[str, int]] = set()

    for index, raw_entry in enumerate(
        _manifest_entries(
            manifest_path,
            lane["manifest_format"],
            payload=manifest_payload,
        ),
        1,
    ):
        entry = _normalize_entry(raw_entry, lane)
        label = f"{manifest_path}: entry {index}"
        raw_action = entry.get("action")
        if not isinstance(raw_action, str) or not raw_action.strip():
            raise GateError(f"{label} needs an explicit action")
        action = raw_action.strip().lower()
        if action not in KNOWN_ACTIONS:
            raise GateError(f"{label} has unsupported action {raw_action!r}")
        entry["action"] = action
        reasons = entry.get("reason_codes")
        if not isinstance(reasons, list) or any(
            not isinstance(reason, str) or not reason.strip() for reason in reasons
        ):
            raise GateError(f"{label} reason_codes must be a list of non-empty strings")
        if action in REPAIR_ACTIONS | NO_OUTPUT_ACTIONS and not reasons:
            raise GateError(f"{label} action {action!r} needs at least one reason code")
        if entry["declared_transform"] != lane["transform"]:
            raise GateError(
                f"{label} declares transform {entry['declared_transform']!r}; "
                f"expected {lane['transform']!r}"
            )
        if entry["declared_version"] != lane["version"]:
            raise GateError(
                f"{label} declares version {entry['declared_version']!r}; "
                f"expected {lane['version']!r}"
            )
        source_path = _logical_source_path(entry["source_path"], f"{label} source_path")
        source_line = entry["source_line"]
        if not isinstance(source_line, int) or isinstance(source_line, bool) or source_line < 1:
            raise GateError(f"{label} source_line must be a positive integer")
        source_key = (source_path, source_line)
        if source_key in seen_sources:
            raise GateError(f"{label} duplicates source identity {source_path}:{source_line}")
        seen_sources.add(source_key)
        entry["source_path"] = source_path
        entry["source_hash"] = _normalized_sha256(entry.get("source_hash"), f"{label} source hash")
        source = source_records.get(source_key)
        if source is None:
            raise GateError(f"{label} source identity is absent from the declared source_run")
        if entry["source_hash"] != source["source_hash"]:
            raise GateError(f"{label} source hash does not match the declared source_run bytes")
        entry["_source_key"] = source_key
        entry["_source_record"] = source["record"]

        output_hash = entry.get("output_hash")
        if output_hash is None:
            if action not in NO_OUTPUT_ACTIONS:
                raise GateError(f"{label} action {action!r} has no authenticated output hash")
        else:
            if action not in OUTPUT_ACTIONS:
                raise GateError(f"{label} action {action!r} cannot declare an output hash")
            if source["record"] is None:
                raise GateError(
                    f"{label} cannot emit a record for an unparseable source line: "
                    f"{source['parse_error']}"
                )
            output_hash = _normalized_sha256(output_hash, f"{label} output hash")
            entry["output_hash"] = output_hash
            if lane["transform"] == "curate_identity":
                entry["_source_originals_sha256"] = _authenticate_identity_source_claims(
                    entry,
                    source["record"],
                    label,
                )
            match_path = (
                "" if lane["transform"] == "same-context-preference-curation" else source_path
            )
            expected_by_path_hash[(match_path, output_hash)].append(entry)
        entries.append(entry)

    outputs_dir = lane["outputs_dir"]
    excluded_paths = {manifest_path, *(item["source_path"] for item in lane["artifacts"])}
    payload_paths = [path for path in _all_jsonl_paths(outputs_dir) if path not in excluded_paths]
    if not payload_paths:
        raise GateError(
            f"lane {lane['order']} ({lane['transform']}) contributed no corpus *.jsonl: "
            f"{outputs_dir}"
        )

    actual_by_path_hash: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    input_files: list[dict[str, Any]] = []
    for path in payload_paths:
        _assert_no_symlink(
            outputs_dir,
            path,
            f"lane {lane['order']} ({lane['transform']}) output",
        )
        relative = path.relative_to(outputs_dir).as_posix()
        records = 0
        payload, payload_sha256, payload_bytes = _read_regular_file_snapshot(
            path,
            f"lane {lane['order']} ({lane['transform']}) output",
        )
        try:
            text = payload.decode("utf-8")
        except UnicodeError as exc:
            raise GateError(f"cannot decode lane output {path}: {exc}") from exc
        for line_number, line in enumerate(_lf_lines(text), 1):
            if not line.strip():
                continue
            records += 1
            try:
                record = json.loads(line, parse_constant=reject_json_constant)
            except (json.JSONDecodeError, ValueError) as exc:
                raise GateError(f"{path}:{line_number}: invalid lane output JSON: {exc}") from exc
            digest = record_sha256(record)
            match_path = "" if lane["transform"] == "same-context-preference-curation" else relative
            actual_by_path_hash[(match_path, digest)].append(
                {
                    "relative_path": relative,
                    "output_line": line_number,
                    "record": record,
                    "output_hash": digest,
                }
            )
        input_files.append(
            {
                "lane_order": lane["order"],
                "transform": lane["transform"],
                "path": relative,
                "sha256": payload_sha256,
                "bytes": payload_bytes,
                "records": records,
            }
        )

    expected_counts = Counter({key: len(items) for key, items in expected_by_path_hash.items()})
    actual_counts = Counter({key: len(items) for key, items in actual_by_path_hash.items()})
    if expected_counts != actual_counts:
        missing = [
            f"{path}@{digest}"
            for path, digest in sorted((expected_counts - actual_counts).elements())[:10]
        ]
        extra = [
            f"{path}@{digest}"
            for path, digest in sorted((actual_counts - expected_counts).elements())[:10]
        ]
        raise GateError(
            f"lane {lane['order']} ({lane['transform']}) output records do not match "
            f"its manifest: missing_hashes={missing}, extra_hashes={extra}"
        )

    records: list[dict[str, Any]] = []
    for path_digest in sorted(expected_by_path_hash):
        expected = sorted(expected_by_path_hash[path_digest], key=lambda item: item["_source_key"])
        actual = sorted(
            actual_by_path_hash[path_digest],
            key=lambda item: (item["relative_path"], item["output_line"]),
        )
        if lane["transform"] == "same-context-preference-curation" and len(expected) > 1:
            sources = [f"{item['source_path']}:{item['source_line']}" for item in expected]
            raise GateError(
                "same-context preference manifest maps multiple source identities to one "
                f"indistinguishable output digest {path_digest[1]}: {sources}"
            )
        for entry, emitted in zip(expected, actual):
            actual_output_id = canonical_record_id(emitted["record"])
            if entry.get("output_id") != actual_output_id:
                raise GateError(
                    f"{manifest_path}: output_id {entry.get('output_id')!r} does not "
                    f"match authenticated output record {emitted['relative_path']}:"
                    f"{emitted['output_line']} id {actual_output_id!r}"
                )
            source_record_sha256 = record_sha256(entry["_source_record"])
            entry["content_changed"] = emitted["output_hash"] != source_record_sha256
            records.append(
                {
                    **emitted,
                    "source_path": entry["source_path"],
                    "source_line": entry["source_line"],
                    "source_key": entry["_source_key"],
                    "source_record": copy.deepcopy(entry["_source_record"]),
                    "source_hash": entry["source_hash"],
                    "source_record_sha256": source_record_sha256,
                    "output_id": actual_output_id,
                    "lane_order": lane["order"],
                    "transform": lane["transform"],
                    "version": lane["version"],
                }
            )

    if not records:
        raise GateError(
            f"lane {lane['order']} ({lane['transform']}) contributed zero records: {outputs_dir}"
        )

    prepared_artifacts: list[dict[str, Any]] = []
    for artifact in lane["artifacts"]:
        artifact_payload, artifact_sha256, artifact_bytes = _read_regular_file_snapshot(
            artifact["source_path"],
            f"lane {lane['order']} ({lane['transform']}) governance artifact",
        )
        catalog: dict[str, dict[str, Any]] | None = None
        if artifact["kind"] == REWARD_CALIBRATION_KIND:
            try:
                catalog = curate_rewards.load_units_migration_bytes(
                    artifact_payload,
                    label=str(artifact["source_path"]),
                )
            except curate_rewards.RewardOntologyError as exc:
                raise GateError(
                    f"lane {lane['order']} calibration artifact is invalid: {exc}"
                ) from exc
            documents = []
        else:
            documents = _load_reward_sidecars(
                artifact["source_path"],
                payload=artifact_payload,
            )
        prepared_artifacts.append(
            {
                **artifact,
                "_payload": artifact_payload,
                "_sha256": artifact_sha256,
                "_bytes": artifact_bytes,
                "_documents": len(documents),
                "_catalog": catalog,
            }
        )

    return {
        **lane,
        "artifacts": prepared_artifacts,
        "entries": entries,
        "records": sorted(
            records,
            key=lambda item: (item["relative_path"], item["output_line"]),
        ),
        "input_files": input_files,
        "manifest_payload": manifest_payload,
        "manifest_sha256": manifest_sha256,
        "manifest_bytes": manifest_bytes,
    }


def prepare_lanes(plan: dict[str, Any]) -> list[dict[str, Any]]:
    source_records = _load_source_records(plan["source_run_dir"])
    prepared = [_prepare_lane(lane, source_records) for lane in plan["lanes"]]
    dispositioned = {emitted["source_key"] for lane in prepared for emitted in lane["records"]}
    dispositioned.update(
        entry["_source_key"]
        for lane in prepared
        for entry in lane["entries"]
        if str(entry.get("action") or "").strip().lower() in EXCLUSION_ACTIONS | QUARANTINE_ACTIONS
    )
    missing = sorted(set(source_records) - dispositioned)
    if missing:
        preview = [f"{path}:{line}" for path, line in missing[:10]]
        raise GateError(
            "source_run records lack a retained output or an explicit exclusion/quarantine: "
            f"count={len(missing)}, first={preview}"
        )
    return prepared


def compose(
    plan: dict[str, Any],
    destination: Path,
    *,
    logical_destination: Path | None = None,
    prepared_lanes: Sequence[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Three-way-compose authenticated lane deltas by source identity."""
    destination = Path(destination).resolve()
    logical_destination = Path(logical_destination or destination).resolve()
    _assert_disjoint_trees(
        plan["source_run_dir"],
        logical_destination,
        source_label="source_run",
        destination_label="cleaned destination",
    )
    _assert_new_destination(destination, "cleaned destination")
    prepared_lanes = list(prepared_lanes or prepare_lanes(plan))

    for lane in prepared_lanes:
        outputs_dir = lane["outputs_dir"]
        if outputs_dir == logical_destination or logical_destination in outputs_dir.parents:
            raise GateError(
                f"lane {lane['order']} ({lane['transform']}) outputs live inside the "
                f"cleaned destination: {outputs_dir}"
            )
        if outputs_dir in logical_destination.parents:
            raise GateError(
                f"cleaned destination is nested inside lane {lane['order']} "
                f"({lane['transform']}) outputs: {outputs_dir}"
            )

    try:
        destination.mkdir(parents=True)
    except FileExistsError as exc:
        raise GateError(
            f"refusing to overwrite an existing cleaned destination: {destination}"
        ) from exc

    state: dict[tuple[str, int], dict[str, Any]] = {}
    terminal_actions: dict[tuple[str, int], dict[str, Any]] = {}
    supersessions: list[dict[str, Any]] = []
    lane_summaries: list[dict[str, Any]] = []
    inputs: list[dict[str, Any]] = []

    for lane in prepared_lanes:
        for entry in lane["entries"]:
            action = str(entry.get("action") or "").strip().lower()
            if action not in EXCLUSION_ACTIONS | QUARANTINE_ACTIONS:
                continue
            terminal_actions[entry["_source_key"]] = entry
            previous = state.pop(entry["_source_key"], None)
            if previous is not None:
                supersessions.append(
                    {
                        "source_path": entry["source_path"],
                        "source_line": entry["source_line"],
                        "superseded_path": previous["relative_path"],
                        "superseded_transform": previous["transform"],
                        "superseded_order": previous["lane_order"],
                        "superseded_sha256": previous["output_hash"],
                        "winning_transform": lane["transform"],
                        "winning_order": lane["order"],
                        "winning_action": action,
                        "winning_sha256": None,
                    }
                )

        for emitted in lane["records"]:
            terminal = terminal_actions.get(emitted["source_key"])
            if terminal is not None:
                supersessions.append(
                    {
                        "source_path": emitted["source_path"],
                        "source_line": emitted["source_line"],
                        "suppressed_path": emitted["relative_path"],
                        "suppressed_transform": lane["transform"],
                        "suppressed_order": lane["order"],
                        "suppressed_sha256": emitted["output_hash"],
                        "winning_transform": terminal["transform"],
                        "winning_order": terminal["lane_order"],
                        "winning_action": terminal["action"],
                        "winning_sha256": None,
                    }
                )
                continue
            previous = state.get(emitted["source_key"])
            if previous is not None:
                merged_record = _merge_lane_delta(
                    emitted["source_record"],
                    previous["record"],
                    emitted["record"],
                    source_key=emitted["source_key"],
                    transform=lane["transform"],
                )
                merged_hash = record_sha256(merged_record)
                supersessions.append(
                    {
                        "source_path": emitted["source_path"],
                        "source_line": emitted["source_line"],
                        "superseded_path": previous["relative_path"],
                        "superseded_transform": previous["transform"],
                        "superseded_order": previous["lane_order"],
                        "superseded_sha256": previous["output_hash"],
                        "winning_path": emitted["relative_path"],
                        "winning_transform": lane["transform"],
                        "winning_order": lane["order"],
                        "winning_action": "record_composition",
                        "winning_lane_output_sha256": emitted["output_hash"],
                        "winning_sha256": merged_hash,
                    }
                )
                state[emitted["source_key"]] = {
                    **emitted,
                    "record": merged_record,
                    "output_hash": merged_hash,
                    "lane_output_hash": emitted["output_hash"],
                    "lineage": [
                        *previous["lineage"],
                        {
                            "lane_order": lane["order"],
                            "transform": lane["transform"],
                            "version": lane["version"],
                            "output_sha256": emitted["output_hash"],
                        },
                    ],
                }
                continue
            state[emitted["source_key"]] = {
                **emitted,
                "lane_output_hash": emitted["output_hash"],
                "lineage": [
                    {
                        "lane_order": lane["order"],
                        "transform": lane["transform"],
                        "version": lane["version"],
                        "output_sha256": emitted["output_hash"],
                    }
                ],
            }

        inputs.extend(lane["input_files"])
        lane_summaries.append(
            {
                "order": lane["order"],
                "bead": lane["bead"],
                "transform": lane["transform"],
                "version": lane["version"],
                "outputs": str(lane["outputs_dir"]),
                "manifest": str(lane["manifest_path"]),
                "files": len(lane["input_files"]),
                "records": len(lane["records"]),
            }
        )

    if not state:
        raise GateError("record-level lane composition produced an empty corpus")

    by_path: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for emitted in state.values():
        by_path[emitted["relative_path"]].append(emitted)

    outputs: list[dict[str, Any]] = []
    record_bindings: list[dict[str, Any]] = []
    for relative, records in sorted(by_path.items()):
        records.sort(key=lambda item: (item["source_path"], item["source_line"]))
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = "".join(
            json.dumps(
                item["record"],
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
            for item in records
        )
        target.write_text(payload, encoding="utf-8", newline="\n")
        for output_line, item in enumerate(records, 1):
            record_bindings.append(
                {
                    "output_path": relative,
                    "output_line": output_line,
                    "output_sha256": item["output_hash"],
                    "output_id": canonical_record_id(item["record"]),
                    "source_path": item["source_path"],
                    "source_line": item["source_line"],
                    "source_hash": item["source_hash"],
                    "source_record_sha256": item["source_record_sha256"],
                    "lineage": copy.deepcopy(item["lineage"]),
                }
            )
        lineage = sorted(
            {
                (
                    contributor["lane_order"],
                    contributor["transform"],
                    contributor["version"],
                    contributor["output_sha256"],
                )
                for item in records
                for contributor in item["lineage"]
            }
        )
        outputs.append(
            {
                "path": relative,
                "sha256": file_sha256(target),
                "bytes": target.stat().st_size,
                "records": len(records),
                "lineage": [
                    {
                        "lane_order": order,
                        "transform": transform,
                        "version": version,
                        "output_sha256": output_sha256,
                    }
                    for order, transform, version, output_sha256 in lineage
                ],
            }
        )

    return {
        "destination": logical_destination,
        "composition_order": lane_summaries,
        "inputs": inputs,
        "outputs": outputs,
        "record_bindings": record_bindings,
        "supersessions": supersessions,
    }


# ---------------------------------------------------------------------------
# lane manifests: exclusions, quarantines, action counts
# ---------------------------------------------------------------------------


def _manifest_entries(
    path: Path,
    format_hint: str | None = None,
    *,
    payload: bytes | None = None,
) -> list[dict[str, Any]]:
    if format_hint not in {None, "json", "jsonl"}:
        raise GateError(f"{path}: unsupported manifest format {format_hint!r}")
    if payload is None:
        payload, _digest, _size = _read_regular_file_snapshot(path, "lane manifest")
    try:
        text = payload.decode("utf-8")
    except UnicodeError as exc:
        raise GateError(f"cannot decode lane manifest {path}: {exc}") from exc
    if format_hint == "jsonl" or (format_hint is None and path.suffix == ".jsonl"):
        entries = []
        for number, line in enumerate(_lf_lines(text), 1):
            if not line.strip():
                continue
            try:
                entry = json.loads(line, parse_constant=reject_json_constant)
            except (json.JSONDecodeError, ValueError) as exc:
                raise GateError(f"{path}:{number}: invalid JSON manifest line: {exc}") from exc
            if not isinstance(entry, dict):
                raise GateError(f"{path}:{number}: manifest entry must be an object")
            entries.append(entry)
        return entries

    try:
        document = json.loads(text, parse_constant=reject_json_constant)
    except (json.JSONDecodeError, ValueError) as exc:
        raise GateError(f"{path}: invalid JSON: {exc}") from exc
    if isinstance(document, list):
        candidates = document
    elif isinstance(document, dict):
        candidates = None
        for key in MANIFEST_LIST_KEYS:
            value = document.get(key)
            if isinstance(value, list):
                candidates = value
                break
        if candidates is None:
            raise GateError(
                f"{path}: manifest object needs one of {', '.join(MANIFEST_LIST_KEYS)} as a list"
            )
    else:
        raise GateError(f"{path}: manifest must be a list or an object")
    for entry in candidates:
        if not isinstance(entry, dict):
            raise GateError(f"{path}: every manifest entry must be an object")
    return list(candidates)


def _normalize_entry(entry: dict[str, Any], lane: dict[str, Any]) -> dict[str, Any]:
    source = entry.get("source")
    if not isinstance(source, dict):
        source = {}
    transform_value = entry.get("transform")
    if isinstance(transform_value, dict):
        transform = transform_value
        transform_name = transform.get("name")
        transform_version = transform.get("version")
    else:
        transform_name = transform_value if isinstance(transform_value, str) else None
        transform_version = None
    declared_transform = entry.get("transform_name") or transform_name
    declared_version = entry.get("transform_version") or transform_version
    reasons = entry.get("reason_codes")
    if reasons is None:
        reasons = []
    return {
        "lane_order": lane["order"],
        "transform": declared_transform or lane["transform"],
        "version": declared_version or lane["version"],
        "declared_transform": declared_transform,
        "declared_version": declared_version,
        "action": entry.get("action"),
        "reason_codes": copy.deepcopy(reasons),
        "source_path": entry.get("source_path") or source.get("path"),
        "source_line": (
            entry.get("source_line") if entry.get("source_line") is not None else source.get("line")
        ),
        "source_hash": (
            entry.get("source_hash") or entry.get("source_sha256") or source.get("sha256")
        ),
        "record_kind": entry.get("record_kind") or entry.get("kind"),
        "classification": entry.get("classification"),
        "output_id": entry.get("output_id"),
        "output_hash": entry.get("output_hash") or entry.get("output_sha256"),
        "id_mappings": copy.deepcopy(entry.get("id_mappings")),
        "provenance_mappings": copy.deepcopy(entry.get("provenance_mappings")),
        "manifest_entry_sha256": record_sha256(entry),
    }


def _public_manifest_entry(entry: dict[str, Any]) -> dict[str, Any]:
    return {key: copy.deepcopy(value) for key, value in entry.items() if not key.startswith("_")}


def collect_lane_manifests(
    prepared_lanes: Sequence[dict[str, Any]],
    retained_source_keys: set[tuple[str, int]] | None = None,
    source_record_sha256_by_key: dict[tuple[str, int], str] | None = None,
) -> dict[str, Any]:
    """Fold every lane's record-level manifest into exclusions and counts."""
    exclusions: list[dict[str, Any]] = []
    quarantines: list[dict[str, Any]] = []
    repairs: list[dict[str, Any]] = []
    review_candidates: list[dict[str, Any]] = []
    actions_by_lane: dict[str, dict[str, int]] = {}
    reason_counts: Counter[str] = Counter()
    identity_mappings: list[dict[str, Any]] = []

    for lane in prepared_lanes:
        counts: Counter[str] = Counter()
        for entry in lane["entries"]:
            normalized = _public_manifest_entry(entry)
            source_key = entry.get("_source_key")
            if retained_source_keys is not None and source_key not in retained_source_keys:
                # ``content_changed`` is derived from a source record that is
                # intentionally absent after a later terminal disposition.
                # Keep the repair action/reasons, but omit this non-replayable
                # convenience field in both integration and promotion views.
                normalized.pop("content_changed", None)
            if (
                source_record_sha256_by_key is not None
                and source_key in source_record_sha256_by_key
                and normalized.get("output_hash") is not None
                and (retained_source_keys is None or source_key in retained_source_keys)
            ):
                normalized["content_changed"] = (
                    normalized["output_hash"] != source_record_sha256_by_key[source_key]
                )
            action = normalized["action"]
            key = str(action) if action is not None else "unspecified"
            counts[key] += 1
            lowered = key.strip().lower()
            if lowered in EXCLUSION_ACTIONS:
                exclusions.append(normalized)
                review_candidates.append(normalized)
                reason_counts.update(normalized["reason_codes"] or ["UNSPECIFIED"])
            elif lowered in QUARANTINE_ACTIONS:
                quarantines.append(normalized)
                review_candidates.append(normalized)
                reason_counts.update(normalized["reason_codes"] or ["UNSPECIFIED"])
            elif lowered in REPAIR_ACTIONS:
                repairs.append(normalized)
                review_candidates.append(normalized)
            elif (
                lowered in RETAIN_ACTIONS
                and normalized.get("content_changed")
                and (retained_source_keys is None or source_key in retained_source_keys)
            ):
                derived = copy.deepcopy(normalized)
                derived["review_action"] = "changed"
                derived["review_reason_codes"] = [DERIVED_CHANGE_REASON]
                review_candidates.append(derived)
            if (
                lane["transform"] == "curate_identity"
                and lowered == "retained"
                and (
                    retained_source_keys is None or entry.get("_source_key") in retained_source_keys
                )
            ):
                normalized["source_originals_sha256"] = _normalized_sha256(
                    entry.get("_source_originals_sha256"),
                    "retained identity source originals",
                )
                identity_mappings.append(normalized)
        actions_by_lane[lane["transform"]] = dict(sorted(counts.items()))

    return {
        "actions_by_lane": actions_by_lane,
        "lanes_without_manifest": [],
        "exclusions": exclusions,
        "quarantines": quarantines,
        "repairs": repairs,
        "identity_mappings": identity_mappings,
        "review_candidates": review_candidates,
        "reason_codes": dict(sorted(reason_counts.items())),
    }


def _load_reward_sidecars(
    path: Path,
    *,
    payload: bytes | None = None,
) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    if payload is None:
        payload, _digest, _size = _read_regular_file_snapshot(path, "reward sidecars")
    try:
        text = payload.decode("utf-8")
    except UnicodeError as exc:
        raise GateError(f"cannot decode reward sidecars {path}: {exc}") from exc
    for line_number, line in enumerate(_lf_lines(text), 1):
        if not line.strip():
            continue
        try:
            document = json.loads(line, parse_constant=reject_json_constant)
        except (json.JSONDecodeError, ValueError) as exc:
            raise GateError(f"{path}:{line_number}: invalid reward sidecar JSON: {exc}") from exc
        if (
            not isinstance(document, dict)
            or document.get("document_type") != "reward_source_sidecar"
        ):
            raise GateError(f"{path}:{line_number}: expected a reward_source_sidecar document")
        try:
            curate_rewards.validate_ontology_document(document)
        except curate_rewards.RewardOntologyError as exc:
            raise GateError(f"{path}:{line_number}: invalid reward sidecar: {exc}") from exc
        documents.append(document)
    if not documents:
        raise GateError(f"{path}: reward sidecar artifact is empty")
    ids = [document["sidecar_id"] for document in documents]
    if len(ids) != len(set(ids)):
        raise GateError(f"{path}: duplicate reward sidecar_id")
    return documents


def copy_lane_evidence(
    prepared_lanes: Sequence[dict[str, Any]], destination: Path
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Copy authenticated manifests/artifacts into the cleaned governance tree."""
    lane_evidence: list[dict[str, Any]] = []
    governance_outputs: list[dict[str, Any]] = []
    for lane in prepared_lanes:
        lane_token = f"{lane['order']:02d}"
        manifest_relative = (
            Path(GOVERNANCE_DIRNAME)
            / LANE_MANIFEST_DIRNAME
            / lane_token
            / f"manifest{lane['manifest_path'].suffix}.evidence"
        )
        manifest_target = destination / manifest_relative
        manifest_target.parent.mkdir(parents=True, exist_ok=True)
        manifest_target.write_bytes(lane["manifest_payload"])
        if file_sha256(manifest_target) != lane["manifest_sha256"]:
            raise GateError(f"lane manifest copy hash mismatch: {lane['manifest_path']}")
        manifest_evidence = {
            "path": manifest_relative.as_posix(),
            "sha256": lane["manifest_sha256"],
            "bytes": lane["manifest_bytes"],
            "format": lane["manifest_format"],
        }
        governance_outputs.append({**manifest_evidence, "kind": "lane_manifest"})

        artifact_evidence: list[dict[str, Any]] = []
        for artifact in lane["artifacts"]:
            artifact_relative = (
                Path(GOVERNANCE_DIRNAME)
                / (
                    REWARD_CALIBRATION_DIRNAME
                    if artifact["kind"] == REWARD_CALIBRATION_KIND
                    else REWARD_SIDECAR_DIRNAME
                )
                / lane_token
                / f"{artifact['destination']}.evidence"
            )
            target = destination / artifact_relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(artifact["_payload"])
            digest = artifact["_sha256"]
            if file_sha256(target) != digest:
                raise GateError(
                    f"governance artifact copy hash mismatch: {artifact['source_path']}"
                )
            evidence = {
                "kind": artifact["kind"],
                "path": artifact_relative.as_posix(),
                "sha256": digest,
                "bytes": artifact["_bytes"],
                "documents": artifact["_documents"],
            }
            artifact_evidence.append(evidence)
            governance_outputs.append(evidence)

        lane_evidence.append(
            {
                "lane_order": lane["order"],
                "bead": lane["bead"],
                "transform": lane["transform"],
                "version": lane["version"],
                "manifest": manifest_evidence,
                "artifacts": artifact_evidence,
            }
        )
    return lane_evidence, governance_outputs


def _evidence_file(cleaned: Path, value: Any, label: str) -> Path:
    relative = _relative_artifact_destination(value, label)
    path = cleaned / relative
    if not path.is_file():
        raise GateError(f"{label} is missing: {path}")
    _assert_no_symlink(cleaned, path, label)
    return path


def verify_lane_evidence(
    cleaned: Path,
    manifest: dict[str, Any],
    retained_source_keys: set[tuple[str, int]] | None = None,
    source_record_sha256_by_key: dict[tuple[str, int], str] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Rebuild lane decisions only from the sealed copies in ``cleaned``."""
    raw_evidence = manifest.get("lane_evidence")
    if not isinstance(raw_evidence, list) or len(raw_evidence) != len(REQUIRED_LANES):
        raise GateError("curation manifest needs evidence for all six lanes")

    expected_files: set[str] = set()
    expected_governance_outputs: list[dict[str, Any]] = []
    prepared: list[dict[str, Any]] = []
    declared: list[tuple[Any, Any]] = []
    for index, evidence in enumerate(raw_evidence, 1):
        if not isinstance(evidence, dict):
            raise GateError(f"lane_evidence[{index}] must be an object")
        order = evidence.get("lane_order")
        transform = evidence.get("transform")
        version = evidence.get("version")
        bead = evidence.get("bead")
        declared.append((bead, transform))
        if order != index or not isinstance(version, str):
            raise GateError(f"lane_evidence[{index}] has invalid lane metadata")
        manifest_meta = evidence.get("manifest")
        if not isinstance(manifest_meta, dict):
            raise GateError(f"lane_evidence[{index}].manifest must be an object")
        manifest_path = _evidence_file(
            cleaned, manifest_meta.get("path"), f"lane_evidence[{index}].manifest"
        )
        expected_files.add(manifest_path.relative_to(cleaned).as_posix())
        expected_sha = _normalized_sha256(
            manifest_meta.get("sha256"), f"lane_evidence[{index}].manifest.sha256"
        )
        manifest_payload, actual_manifest_sha, manifest_bytes = _read_regular_file_snapshot(
            manifest_path,
            f"lane_evidence[{index}] manifest",
        )
        if actual_manifest_sha != expected_sha:
            raise GateError(f"lane_evidence[{index}] manifest hash mismatch")
        if manifest_meta.get("bytes") != manifest_bytes:
            raise GateError(f"lane_evidence[{index}] manifest byte count mismatch")
        expected_governance_outputs.append(
            {
                "path": manifest_path.relative_to(cleaned).as_posix(),
                "sha256": expected_sha,
                "bytes": manifest_bytes,
                "format": manifest_meta.get("format"),
                "kind": "lane_manifest",
            }
        )

        lane = {
            "order": index,
            "bead": bead,
            "transform": transform,
            "version": version,
            "manifest_path": manifest_path,
        }
        entries: list[dict[str, Any]] = []
        seen_sources: set[tuple[str, int]] = set()
        manifest_format = manifest_meta.get("format")
        if manifest_format not in {"json", "jsonl"}:
            raise GateError(f"lane_evidence[{index}].manifest has invalid format metadata")
        for entry_index, raw_entry in enumerate(
            _manifest_entries(
                manifest_path,
                manifest_format,
                payload=manifest_payload,
            ),
            1,
        ):
            entry = _normalize_entry(raw_entry, lane)
            label = f"{manifest_path}: entry {entry_index}"
            if entry["declared_transform"] != transform or entry["declared_version"] != version:
                raise GateError(f"{label} no longer matches its lane contract")
            source_path = _logical_source_path(entry["source_path"], f"{label} source_path")
            source_line = entry["source_line"]
            if not isinstance(source_line, int) or isinstance(source_line, bool) or source_line < 1:
                raise GateError(f"{label} source_line must be a positive integer")
            source_key = (source_path, source_line)
            if source_key in seen_sources:
                raise GateError(f"{label} duplicates source identity {source_path}:{source_line}")
            seen_sources.add(source_key)
            entry["source_path"] = source_path
            entry["source_hash"] = _normalized_sha256(
                entry.get("source_hash"), f"{label} source hash"
            )
            entry["_source_key"] = source_key
            if entry.get("output_hash") is not None:
                entry["output_hash"] = _normalized_sha256(
                    entry["output_hash"], f"{label} output hash"
                )
            entries.append(entry)

        artifacts = evidence.get("artifacts", [])
        if not isinstance(artifacts, list):
            raise GateError(f"lane_evidence[{index}].artifacts must be a list")
        for artifact_index, artifact in enumerate(artifacts, 1):
            if not isinstance(artifact, dict) or artifact.get("kind") not in REWARD_ARTIFACT_KINDS:
                raise GateError(f"lane_evidence[{index}].artifacts[{artifact_index}] is invalid")
            artifact_path = _evidence_file(
                cleaned,
                artifact.get("path"),
                f"lane_evidence[{index}].artifacts[{artifact_index}]",
            )
            expected_files.add(artifact_path.relative_to(cleaned).as_posix())
            expected_sha = _normalized_sha256(
                artifact.get("sha256"),
                f"lane_evidence[{index}].artifacts[{artifact_index}].sha256",
            )
            artifact_payload, actual_artifact_sha, artifact_bytes = _read_regular_file_snapshot(
                artifact_path,
                f"lane_evidence[{index}] artifact {artifact_index}",
            )
            if actual_artifact_sha != expected_sha:
                raise GateError(f"lane_evidence[{index}] artifact hash mismatch")
            catalog = None
            if artifact.get("kind") == REWARD_CALIBRATION_KIND:
                try:
                    catalog = curate_rewards.load_units_migration_bytes(
                        artifact_payload,
                        label=artifact_path.as_posix(),
                    )
                except curate_rewards.RewardOntologyError as exc:
                    raise GateError(
                        f"lane_evidence[{index}] calibration artifact is invalid: {exc}"
                    ) from exc
                documents: list[dict[str, Any]] = []
            else:
                documents = _load_reward_sidecars(artifact_path, payload=artifact_payload)
            if artifact.get("documents") != len(documents):
                raise GateError(f"lane_evidence[{index}] artifact document count mismatch")
            if artifact.get("bytes") != artifact_bytes:
                raise GateError(f"lane_evidence[{index}] artifact byte count mismatch")
            expected_governance_outputs.append(
                {
                    "kind": artifact.get("kind"),
                    "path": artifact_path.relative_to(cleaned).as_posix(),
                    "sha256": expected_sha,
                    "bytes": artifact_bytes,
                    "documents": len(documents),
                }
            )
            artifacts_for_lane = lane.setdefault("artifacts", [])
            artifacts_for_lane.append(
                {
                    "kind": artifact.get("kind"),
                    "source_path": artifact_path,
                    "_catalog": catalog,
                }
            )
        prepared.append({**lane, "entries": entries})

    if tuple(declared) != REQUIRED_LANES:
        raise GateError("lane evidence does not match the six required contracts in order")
    actual_files = {
        path.relative_to(cleaned).as_posix()
        for path in sorted((cleaned / GOVERNANCE_DIRNAME).rglob("*"))
        if path.is_file()
    }
    if actual_files != expected_files:
        raise GateError(
            "governance evidence file set mismatch: "
            f"missing={sorted(expected_files - actual_files)}, "
            f"extra={sorted(actual_files - expected_files)}"
        )
    if manifest.get("governance_outputs") != expected_governance_outputs:
        raise GateError("governance_outputs metadata does not match copied evidence bytes")

    raw_identity_mappings = manifest.get("identity_mappings")
    if not isinstance(raw_identity_mappings, list):
        raise GateError("curation manifest needs retained identity mappings")
    attestations: dict[tuple[str, int, str], str] = {}
    for index, mapping in enumerate(raw_identity_mappings, 1):
        label = f"identity_mappings[{index}]"
        if not isinstance(mapping, dict):
            raise GateError(f"{label} must be an object")
        source_path = _logical_source_path(mapping.get("source_path"), f"{label}.source_path")
        source_line = mapping.get("source_line")
        if not isinstance(source_line, int) or isinstance(source_line, bool) or source_line < 1:
            raise GateError(f"{label}.source_line must be a positive integer")
        manifest_entry_sha256 = _normalized_sha256(
            mapping.get("manifest_entry_sha256"),
            f"{label}.manifest_entry_sha256",
        )
        key = (source_path, source_line, manifest_entry_sha256)
        if key in attestations:
            raise GateError(f"{label} duplicates retained identity evidence")
        attestations[key] = _normalized_sha256(
            mapping.get("source_originals_sha256"),
            f"{label}.source_originals_sha256",
        )

    restored: set[tuple[str, int, str]] = set()
    for lane in prepared:
        if lane["transform"] != "curate_identity":
            continue
        for entry in lane["entries"]:
            source_key = entry["_source_key"]
            action = str(entry.get("action") or "").strip().lower()
            if action not in RETAIN_ACTIONS or (
                retained_source_keys is not None and source_key not in retained_source_keys
            ):
                continue
            key = (*source_key, entry["manifest_entry_sha256"])
            attestation = attestations.get(key)
            if attestation is None:
                raise GateError(
                    "curation manifest lacks source-original attestation for retained "
                    f"identity entry {source_key[0]}:{source_key[1]}"
                )
            entry["_source_originals_sha256"] = attestation
            restored.add(key)
    if restored != set(attestations):
        raise GateError("curation manifest has orphan retained identity attestations")
    return prepared, collect_lane_manifests(
        prepared,
        retained_source_keys,
        source_record_sha256_by_key,
    )


# ---------------------------------------------------------------------------
# final-output bindings and retained identity evidence
# ---------------------------------------------------------------------------


def _normalized_output_path(value: Any, label: str) -> str:
    path = _relative_artifact_destination(value, label)
    if path.suffix != ".jsonl" or path.parts[0] == GOVERNANCE_DIRNAME:
        raise GateError(f"{label} must identify a corpus JSONL path")
    return path.as_posix()


def _normalize_record_bindings(raw_bindings: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_bindings, list) or not raw_bindings:
        raise GateError("curation manifest needs a non-empty record_bindings list")
    normalized: list[dict[str, Any]] = []
    output_coordinates: set[tuple[str, int]] = set()
    source_coordinates: set[tuple[str, int]] = set()
    for index, raw in enumerate(raw_bindings, 1):
        label = f"record_bindings[{index}]"
        if not isinstance(raw, dict):
            raise GateError(f"{label} must be an object")
        output_path = _normalized_output_path(raw.get("output_path"), f"{label}.output_path")
        source_path = _logical_source_path(raw.get("source_path"), f"{label}.source_path")
        output_line = raw.get("output_line")
        source_line = raw.get("source_line")
        for field, value in (("output_line", output_line), ("source_line", source_line)):
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise GateError(f"{label}.{field} must be a positive integer")
        output_coordinate = (output_path, output_line)
        source_coordinate = (source_path, source_line)
        if output_coordinate in output_coordinates:
            raise GateError(f"{label} duplicates output coordinate {output_path}:{output_line}")
        if source_coordinate in source_coordinates:
            raise GateError(f"{label} duplicates source coordinate {source_path}:{source_line}")
        output_coordinates.add(output_coordinate)
        source_coordinates.add(source_coordinate)

        output_id = raw.get("output_id")
        if output_id is not None and (
            not isinstance(output_id, str)
            or not output_id.strip()
            or output_id != output_id.strip()
        ):
            raise GateError(f"{label}.output_id must be null or a normalized non-empty string")
        lineage = raw.get("lineage")
        if not isinstance(lineage, list) or not lineage:
            raise GateError(f"{label}.lineage must be a non-empty list")
        normalized_lineage: list[dict[str, Any]] = []
        seen_lane_orders: set[int] = set()
        for lineage_index, item in enumerate(lineage, 1):
            lineage_label = f"{label}.lineage[{lineage_index}]"
            if not isinstance(item, dict):
                raise GateError(f"{lineage_label} must be an object")
            order = item.get("lane_order")
            if (
                not isinstance(order, int)
                or isinstance(order, bool)
                or not 1 <= order <= len(REQUIRED_LANES)
                or order in seen_lane_orders
            ):
                raise GateError(f"{lineage_label}.lane_order is invalid or duplicated")
            seen_lane_orders.add(order)
            transform = item.get("transform")
            version = item.get("version")
            if transform != REQUIRED_LANES[order - 1][1] or not isinstance(version, str):
                raise GateError(f"{lineage_label} does not match its lane contract")
            normalized_lineage.append(
                {
                    "lane_order": order,
                    "transform": transform,
                    "version": version,
                    "output_sha256": _normalized_sha256(
                        item.get("output_sha256"), f"{lineage_label}.output_sha256"
                    ),
                }
            )
        normalized.append(
            {
                "output_path": output_path,
                "output_line": output_line,
                "output_sha256": _normalized_sha256(
                    raw.get("output_sha256"), f"{label}.output_sha256"
                ),
                "output_id": output_id,
                "source_path": source_path,
                "source_line": source_line,
                "source_hash": _normalized_sha256(raw.get("source_hash"), f"{label}.source_hash"),
                "source_record_sha256": _normalized_sha256(
                    raw.get("source_record_sha256"), f"{label}.source_record_sha256"
                ),
                "lineage": sorted(
                    normalized_lineage, key=lambda lane_row: lane_row["lane_order"]
                ),
            }
        )
    return sorted(
        normalized, key=lambda binding: (binding["output_path"], binding["output_line"])
    )


def _output_evidence_gate(
    cleaned: Path,
    raw_bindings: Any,
    prepared_lanes: Sequence[dict[str, Any]],
) -> tuple[dict[str, Any], dict[tuple[str, int], Any], list[dict[str, Any]]]:
    """Authenticate every final row against source identity and lane evidence."""
    bindings = _normalize_record_bindings(raw_bindings)
    actual_by_output: dict[tuple[str, int], Any] = {}
    errors: list[dict[str, str]] = []
    for relative, line, record in iter_records(cleaned):
        coordinate = (relative, line)
        if record is None:
            errors.append(
                {"source": f"{relative}:{line}", "error": "final output is not valid JSON"}
            )
            continue
        actual_by_output[coordinate] = record

    binding_by_output = {
        (binding["output_path"], binding["output_line"]): binding for binding in bindings
    }
    missing_bindings = sorted(set(actual_by_output) - set(binding_by_output))
    extra_bindings = sorted(set(binding_by_output) - set(actual_by_output))
    for path, line in missing_bindings[:10]:
        errors.append({"source": f"{path}:{line}", "error": "final record has no binding"})
    for path, line in extra_bindings[:10]:
        errors.append({"source": f"{path}:{line}", "error": "binding has no final record"})

    entries_by_source: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    terminal_sources: set[tuple[str, int]] = set()
    for lane in prepared_lanes:
        for entry in lane["entries"]:
            source_key = entry["_source_key"]
            action = str(entry.get("action") or "").strip().lower()
            if action in EXCLUSION_ACTIONS | QUARANTINE_ACTIONS:
                terminal_sources.add(source_key)
            if entry.get("output_hash") is not None:
                entries_by_source[source_key].append(entry)

    expected_source_keys = set(entries_by_source) - terminal_sources
    bound_source_keys = {(binding["source_path"], binding["source_line"]) for binding in bindings}
    for path, line in sorted(expected_source_keys - bound_source_keys)[:10]:
        errors.append(
            {"source": f"{path}:{line}", "error": "retained lane evidence has no final output"}
        )
    for path, line in sorted(bound_source_keys - expected_source_keys)[:10]:
        errors.append(
            {"source": f"{path}:{line}", "error": "final binding has no retained lane evidence"}
        )

    records_by_source: dict[tuple[str, int], Any] = {}
    for coordinate in sorted(set(binding_by_output) & set(actual_by_output)):
        binding = binding_by_output[coordinate]
        record = actual_by_output[coordinate]
        where = f"{coordinate[0]}:{coordinate[1]}"
        if record_sha256(record) != binding["output_sha256"]:
            errors.append({"source": where, "error": "final record hash mismatches binding"})
        if canonical_record_id(record) != binding["output_id"]:
            errors.append({"source": where, "error": "final record id mismatches binding"})
        source_key = (binding["source_path"], binding["source_line"])
        records_by_source[source_key] = record
        evidence_entries = entries_by_source.get(source_key, [])
        source_hashes = {entry.get("source_hash") for entry in evidence_entries}
        if source_hashes != {binding["source_hash"]}:
            errors.append(
                {"source": where, "error": "binding source hash mismatches lane evidence"}
            )
        expected_lineage = sorted(
            (
                entry["lane_order"],
                entry["transform"],
                entry["version"],
                entry["output_hash"],
            )
            for entry in evidence_entries
        )
        actual_lineage = sorted(
            (
                item["lane_order"],
                item["transform"],
                item["version"],
                item["output_sha256"],
            )
            for item in binding["lineage"]
        )
        if actual_lineage != expected_lineage:
            errors.append({"source": where, "error": "binding lineage mismatches lane evidence"})

    report = {
        "tool": "curate_gate final-output binding verifier",
        "passed": not errors,
        "records": len(actual_by_output),
        "bindings": len(bindings),
        "invalid_bindings": len(errors),
        "examples": errors[:5],
    }
    return report, records_by_source, bindings


def _mapping_value(document: Any, pointer: Any, label: str) -> Any:
    if pointer == "/":
        return document
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise GateError(f"{label} must be a JSON pointer")
    value = document
    for raw_token in pointer[1:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            try:
                value = value[int(token)]
            except (ValueError, IndexError) as exc:
                raise GateError(f"{label} does not resolve") from exc
        elif isinstance(value, dict) and token in value:
            value = value[token]
        else:
            raise GateError(f"{label} does not resolve")
    return value


def _mapping_pointer(base: str, key: str) -> str:
    token = key.replace("~", "~0").replace("/", "~1")
    return f"/{token}" if base == "/" else f"{base}/{token}"


def _canonical_identity_output_id(
    source_path: str, source_line: int, kind: str, owner_path: str
) -> str:
    factory = source_path.split("/", 1)[0]
    source = curate_identity.SourceIdentity(
        source_path,
        source_line,
        factory,
        "0" * 64,
        "source-coordinate",
        None,
    )
    return curate_identity.canonical_id(source, kind, owner_path)


def _identity_owner_specs(
    source_record: dict[str, Any],
    kind: str,
    label: str,
) -> list[tuple[str, dict[str, Any]]]:
    if kind == "thalamic":
        return [("/", source_record)]
    if kind == "preference":
        paths = ("/chosen", "/rejected")
    elif kind == "bridge_pair":
        paths = ("/language_view/trajectory",)
    else:
        return []
    owners: list[tuple[str, dict[str, Any]]] = []
    for path in paths:
        owner = _mapping_value(source_record, path, f"{label}{path}")
        if not isinstance(owner, dict):
            raise GateError(f"{label}{path} does not identify a source object")
        owners.append((path, owner))
    return owners


def _source_original_ids(
    source_record: dict[str, Any], owner_path: str, label: str
) -> list[dict[str, Any]]:
    owner = _mapping_value(source_record, owner_path, f"{label}.owner_path")
    if not isinstance(owner, dict):
        raise GateError(f"{label}.owner_path does not identify a source object")
    originals: list[dict[str, Any]] = []
    for container, base in (
        (owner, owner_path),
        (owner.get("meta"), _mapping_pointer(owner_path, "meta")),
        (owner.get("state"), _mapping_pointer(owner_path, "state")),
    ):
        if not isinstance(container, dict):
            continue
        for key in curate_identity.LEGACY_ID_KEYS:
            if key in container:
                originals.append(
                    {
                        "path": _mapping_pointer(base, key),
                        "value": copy.deepcopy(container[key]),
                    }
                )
    return originals


def _source_original_provenance(
    source_record: dict[str, Any], owner_path: str, state_path: str | None, label: str
) -> dict[str, Any]:
    owner = _mapping_value(source_record, owner_path, f"{label}.owner_path")
    if not isinstance(owner, dict):
        raise GateError(f"{label}.owner_path does not identify a source object")
    owner_snapshot = {
        "present": "provenance" in owner,
        "value": copy.deepcopy(owner.get("provenance")),
    }
    if state_path is None:
        return {"owner_provenance": owner_snapshot}
    state = _mapping_value(source_record, state_path, f"{label}.state_path")
    if not isinstance(state, dict):
        raise GateError(f"{label}.state_path does not identify a source object")
    return {
        "sim_or_real": {
            "present": "sim_or_real" in state,
            "value": copy.deepcopy(state.get("sim_or_real")),
        },
        "state_provenance": {
            "present": "provenance" in state,
            "value": copy.deepcopy(state.get("provenance")),
        },
        "owner_provenance": owner_snapshot,
    }


def _claimed_identity_source_evidence(entry: dict[str, Any], label: str) -> dict[str, Any]:
    id_mappings = entry.get("id_mappings")
    provenance_mappings = entry.get("provenance_mappings")
    if not isinstance(id_mappings, list) or not id_mappings:
        raise GateError(f"{label}.id_mappings must be non-empty")
    if not isinstance(provenance_mappings, list) or not provenance_mappings:
        raise GateError(f"{label}.provenance_mappings must be non-empty")
    claimed_ids: list[dict[str, Any]] = []
    for index, mapping in enumerate(id_mappings, 1):
        mapping_label = f"{label}.id_mappings[{index}]"
        if not isinstance(mapping, dict):
            raise GateError(f"{mapping_label} must be an object")
        originals = mapping.get("original_ids")
        if not isinstance(originals, list):
            raise GateError(f"{mapping_label}.original_ids must be a list")
        claimed_ids.append(
            {
                "owner_path": mapping.get("owner_path"),
                "original_ids": copy.deepcopy(originals),
            }
        )
    claimed_provenance: list[dict[str, Any]] = []
    for index, mapping in enumerate(provenance_mappings, 1):
        mapping_label = f"{label}.provenance_mappings[{index}]"
        if not isinstance(mapping, dict):
            raise GateError(f"{mapping_label} must be an object")
        original = mapping.get("original")
        if not isinstance(original, dict):
            raise GateError(f"{mapping_label}.original must be an object")
        claimed_provenance.append(
            {
                "owner_path": mapping.get("owner_path"),
                "state_path": mapping.get("state_path"),
                "original": copy.deepcopy(original),
            }
        )
    return {
        "id_mappings": claimed_ids,
        "provenance_mappings": claimed_provenance,
    }


def _authenticate_identity_source_claims(
    entry: dict[str, Any], source_record: Any, label: str
) -> str:
    if not isinstance(source_record, dict):
        raise GateError(f"{label} cannot authenticate identity claims for a non-object source")
    claimed = _claimed_identity_source_evidence(entry, label)
    try:
        kind = curate_identity.record_kind(source_record)
    except curate_identity.IdentityCurationError as exc:
        raise GateError(f"{label} source record has no supported identity shape: {exc}") from exc
    owners = _identity_owner_specs(source_record, kind, label)
    id_owner_paths = ["/", *(path for path, _owner in owners if path != "/")]
    expected_ids = [
        {
            "owner_path": owner_path,
            "original_ids": _source_original_ids(
                source_record,
                owner_path,
                f"{label}.id_mappings[{index}]",
            ),
        }
        for index, owner_path in enumerate(id_owner_paths, 1)
    ]

    state_owners = owners or [("/", source_record)]
    use_state = any(
        isinstance(state := owner.get("state"), dict)
        and ("sim_or_real" in state or "provenance" in state)
        for _owner_path, owner in state_owners
    )
    provenance_paths: list[tuple[str, str | None]]
    if use_state:
        provenance_paths = []
        for owner_path, owner in state_owners:
            state_path = _mapping_pointer(owner_path, "state")
            if not isinstance(owner.get("state"), dict):
                raise GateError(f"{label}{state_path} does not identify a source object")
            provenance_paths.append((owner_path, state_path))
        if kind in {"preference", "bridge_pair", "episode", "safety_case", "multi_agent"}:
            provenance_paths.append(("/", None))
    else:
        provenance_paths = [("/", None)]
    expected_provenance = [
        {
            "owner_path": owner_path,
            "state_path": state_path,
            "original": _source_original_provenance(
                source_record,
                owner_path,
                state_path,
                f"{label}.provenance_mappings[{index}]",
            ),
        }
        for index, (owner_path, state_path) in enumerate(provenance_paths, 1)
    ]
    expected = {
        "id_mappings": expected_ids,
        "provenance_mappings": expected_provenance,
    }
    if not _same_json(claimed, expected):
        raise GateError(
            f"{label} original identity evidence does not match the source record or is incomplete"
        )
    return record_sha256(expected)


def _identity_mapping_gate(
    identity_entries: Sequence[dict[str, Any]],
    records_by_source: dict[tuple[str, int], Any],
) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    checked_ids = 0
    checked_provenance = 0
    checked_source_originals = 0
    identity_source_keys: set[tuple[str, int]] = set()
    for entry_index, entry in enumerate(identity_entries, 1):
        source_key = (entry.get("source_path"), entry.get("source_line"))
        identity_source_keys.add(source_key)
        where = f"{source_key[0]}:{source_key[1]}"
        record = records_by_source.get(source_key)
        if not isinstance(record, dict):
            errors.append({"source": where, "error": "retained identity mapping has no output"})
            continue
        if entry.get("output_id") != canonical_record_id(record):
            errors.append({"source": where, "error": "identity output_id mismatches final record"})

        try:
            claimed_originals = _claimed_identity_source_evidence(
                entry,
                f"identity_mappings[{entry_index}]",
            )
            expected_originals_sha256 = _normalized_sha256(
                entry.get("source_originals_sha256"),
                f"identity_mappings[{entry_index}].source_originals_sha256",
            )
            if record_sha256(claimed_originals) != expected_originals_sha256:
                raise GateError("original identity evidence mismatches authenticated source")
            checked_source_originals += 1
        except GateError as exc:
            errors.append({"source": where, "error": str(exc)})

        id_mappings = entry.get("id_mappings")
        if not isinstance(id_mappings, list) or not id_mappings:
            errors.append({"source": where, "error": "id_mappings must be non-empty"})
        else:
            seen_owners: set[str] = set()
            try:
                kind = curate_identity.record_kind(record)
            except curate_identity.IdentityCurationError as exc:
                errors.append(
                    {
                        "source": where,
                        "error": f"{where} output has no supported identity shape: {exc}",
                    }
                )
                continue
            for mapping_index, mapping in enumerate(id_mappings, 1):
                label = f"identity_mappings[{entry_index}].id_mappings[{mapping_index}]"
                try:
                    if not isinstance(mapping, dict):
                        raise GateError(f"{label} must be an object")
                    owner_path = mapping.get("owner_path")
                    if owner_path in seen_owners:
                        raise GateError(f"{label} duplicates owner_path {owner_path!r}")
                    seen_owners.add(owner_path)
                    owner = _mapping_value(record, owner_path, f"{label}.owner_path")
                    output_id = mapping.get("output_id")
                    if (
                        not isinstance(owner, dict)
                        or not isinstance(output_id, str)
                        or owner.get("id") != output_id
                    ):
                        raise GateError(f"{label}.output_id does not match output owner")
                    source_path = entry.get("source_path")
                    source_line = entry.get("source_line")
                    if not isinstance(source_path, str) or not isinstance(source_line, int):
                        raise GateError(f"{label} is missing an authenticated source coordinate")
                    expected_id = _canonical_identity_output_id(
                        source_path,
                        source_line,
                        kind,
                        owner_path,
                    )
                    if output_id is not None and output_id != expected_id:
                        raise GateError(
                            f"{label}.output_id is not the deterministic canonical identity"
                        )
                    checked_ids += 1
                except GateError as exc:
                    errors.append({"source": where, "error": str(exc)})

        provenance_mappings = entry.get("provenance_mappings")
        if not isinstance(provenance_mappings, list) or not provenance_mappings:
            errors.append({"source": where, "error": "provenance_mappings must be non-empty"})
        else:
            for mapping_index, mapping in enumerate(provenance_mappings, 1):
                label = f"identity_mappings[{entry_index}].provenance_mappings[{mapping_index}]"
                try:
                    if not isinstance(mapping, dict):
                        raise GateError(f"{label} must be an object")
                    canonical = mapping.get("canonical")
                    if not isinstance(canonical, dict):
                        raise GateError(f"{label}.canonical must be an object")
                    owner = _mapping_value(record, mapping.get("owner_path"), f"{label}.owner_path")
                    if not isinstance(owner, dict) or not _same_json(
                        owner.get("provenance", _MISSING), canonical
                    ):
                        raise GateError(f"{label}.canonical does not match output provenance")
                    state_path = mapping.get("state_path")
                    if state_path is not None:
                        state = _mapping_value(record, state_path, f"{label}.state_path")
                        if (
                            not isinstance(state, dict)
                            or not _same_json(state.get("provenance", _MISSING), canonical)
                            or state.get("sim_or_real") != canonical.get("kind")
                        ):
                            raise GateError(f"{label}.canonical does not match output state")
                    checked_provenance += 1
                except GateError as exc:
                    errors.append({"source": where, "error": str(exc)})

    for source_path, source_line in sorted(set(records_by_source) - identity_source_keys):
        errors.append(
            {
                "source": f"{source_path}:{source_line}",
                "error": "retained record has no authenticated identity mapping",
            }
        )

    return {
        "tool": "curate_gate retained identity/provenance mapping verifier",
        "passed": not errors,
        "retained_entries": len(identity_entries),
        "id_mappings": checked_ids,
        "provenance_mappings": checked_provenance,
        "source_originals": checked_source_originals,
        "invalid_mappings": len(errors),
        "examples": errors[:5],
    }


# ---------------------------------------------------------------------------
# stratified review sample
# ---------------------------------------------------------------------------


def _primary_decision(obj: Any, kind: str) -> str:
    if not isinstance(obj, dict):
        return "none"
    decisions: dict[str, str] = {}
    for role, view in training_audit.thalamic_views(obj, kind):
        decision = training_audit.dict_field(view, "safety_decision").get("decision")
        if isinstance(decision, str) and decision.strip():
            decisions[role] = decision.strip()
    for role in DECISION_ROLE_PRIORITY:
        if role in decisions:
            return decisions[role]
    if decisions:
        return decisions[sorted(decisions)[0]]
    return "none"


def _repair_action(obj: Any) -> str:
    """Repair marker a curation lane left on the record, when there is one."""
    if not isinstance(obj, dict):
        return "none"
    meta = obj.get("meta")
    if isinstance(meta, dict):
        for key in ("curation_action", "transform_action", "repair_action"):
            value = meta.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        if meta.get("spike_events_resorted"):
            return "spike_events_resorted"
    return "none"


def iter_records(root: Path) -> Iterable[tuple[str, int, Any]]:
    """Yield ``(relative_path, line_number, parsed_record)`` for the corpus."""
    for path in jsonl_paths(root):
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for number, line in enumerate(_lf_lines(text), 1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line, parse_constant=reject_json_constant)
            except (json.JSONDecodeError, ValueError):
                yield rel, number, None
                continue
            yield rel, number, obj


def _review_candidates_from_manifest(cleaned: Path) -> list[dict[str, Any]]:
    manifest_path = cleaned / MANIFEST_FILENAME
    if not manifest_path.is_file():
        return []
    manifest = _load_json(manifest_path)
    if not isinstance(manifest, dict):
        raise GateError(f"{manifest_path}: manifest must be a JSON object")
    candidates = manifest.get("review_candidates", [])
    if not isinstance(candidates, list) or not all(
        isinstance(candidate, dict) for candidate in candidates
    ):
        raise GateError(f"{manifest_path}: review_candidates must be a list of objects")
    return candidates


def _manifest_factory(source_path: Any, transform: Any) -> str:
    if isinstance(source_path, str) and source_path.strip():
        parts = Path(source_path).parts
        if "raw" in parts:
            index = parts.index("raw")
            if len(parts) > index + 2:
                return parts[index + 2]
        if len(parts) > 1:
            return parts[0]
    return str(transform or "_manifest")


def build_sample(
    cleaned: Path,
    per_stratum: int = DEFAULT_PER_STRATUM,
    review_candidates: Sequence[dict[str, Any]] | None = None,
    *,
    evidence_digest: str | None = None,
) -> dict[str, Any]:
    """Stratify corpus and manifest decisions, then sample deterministically."""
    cleaned = Path(cleaned).resolve()
    if per_stratum < 1:
        raise GateError("--per-stratum must be at least 1")
    if review_candidates is None:
        review_candidates = _review_candidates_from_manifest(cleaned)
        manifest_path = cleaned / MANIFEST_FILENAME
        if evidence_digest is None and manifest_path.is_file():
            manifest = _load_json(manifest_path)
            if isinstance(manifest, dict):
                value = manifest.get("evidence_digest")
                if isinstance(value, str):
                    evidence_digest = value
    if not all(isinstance(candidate, dict) for candidate in review_candidates):
        raise GateError("review candidates must be objects")

    buckets: dict[tuple[str, str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for rel, number, obj in iter_records(cleaned):
        where = f"{rel}:{number}"
        factory = rel.split("/")[0] if "/" in rel else "_root"
        if obj is None:
            kind = "unparsable"
            decision = "none"
            repair = "none"
            digest = sha256_hex(where.encode("utf-8"))
            record_id = None
        else:
            _errors, kind = check_line(obj, where)
            decision = _primary_decision(obj, kind)
            repair = _repair_action(obj)
            digest = sha256_hex(training_audit.canonical_blob(obj).encode("utf-8"))
            record_id = canonical_record_id(obj) if isinstance(obj, dict) else None
        buckets[("corpus", factory, kind, decision, repair, "none")].append(
            {
                "source": where,
                "record_id": record_id,
                "record_sha256": digest,
            }
        )

    for candidate in review_candidates:
        declared_action = str(candidate.get("action") or "unspecified").strip().lower()
        action = str(candidate.get("review_action") or declared_action).strip().lower()
        reasons = candidate.get("reason_codes")
        if not isinstance(reasons, list):
            reasons = []
        exclusion_reason = "none"
        if action in EXCLUSION_ACTIONS or action in QUARANTINE_ACTIONS:
            exclusion_reason = "+".join(sorted(str(reason) for reason in reasons)) or "UNSPECIFIED"
        transform = candidate.get("transform")
        source_path = candidate.get("source_path")
        source_line = candidate.get("source_line")
        digest = sha256_hex(training_audit.canonical_blob(candidate).encode("utf-8"))
        source = (
            f"manifest:{candidate.get('lane_order')}:{transform}:"
            f"{source_path}:{source_line}:{digest[:16]}"
        )
        repair = action if action in REPAIR_ACTIONS else "none"
        factory = _manifest_factory(source_path, transform)
        kind = str(candidate.get("record_kind") or "manifest_decision")
        buckets[("manifest", factory, kind, action, repair, exclusion_reason)].append(
            {
                "source": source,
                "record_id": candidate.get("output_id"),
                "record_sha256": digest,
                "manifest_entry": candidate,
            }
        )

    strata: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []
    for key in sorted(buckets):
        evidence, factory, kind, decision, repair, exclusion_reason = key
        population = buckets[key]
        # Content-derived order: stable across runs, independent of file order.
        chosen = sorted(
            population,
            key=lambda sampled: (sampled["record_sha256"], sampled["source"]),
        )[
            :per_stratum
        ]
        strata.append(
            {
                "evidence": evidence,
                "factory": factory,
                "kind": kind,
                "decision": decision,
                "repair_action": repair,
                "exclusion_reason": exclusion_reason,
                "population": len(population),
                "sampled": len(chosen),
            }
        )
        for item in chosen:
            items.append(
                {
                    "evidence": evidence,
                    "factory": factory,
                    "kind": kind,
                    "decision": decision,
                    "repair_action": repair,
                    "exclusion_reason": exclusion_reason,
                    **item,
                }
            )

    return {
        "schema": SAMPLE_SCHEMA,
        "generated_by": f"{TOOL_NAME}/{TOOL_VERSION}",
        "cleaned_dir": str(cleaned),
        "corpus_digest": corpus_digest(cleaned),
        "evidence_digest": evidence_digest,
        "per_stratum": per_stratum,
        "strata_count": len(strata),
        "sampled_records": len(items),
        "strata": strata,
        "items": items,
    }


def review_template(sample: dict[str, Any]) -> dict[str, Any]:
    """A fill-in-the-blanks verdict file for the recorded sample."""
    return {
        "schema": REVIEW_SCHEMA,
        "reviewer": "",
        "reviewed_at": "",
        "corpus_digest": sample["corpus_digest"],
        "evidence_digest": sample.get("evidence_digest"),
        "verdicts": {item["source"]: {"verdict": "", "notes": ""} for item in sample["items"]},
    }


def check_review(
    sample: dict[str, Any], review: Any, digest: str, evidence_digest: str
) -> tuple[list[str], dict[str, Any]]:
    """Return ``(blockers, summary)`` for a reviewed stratified sample."""
    blockers: list[str] = []
    if not isinstance(review, dict):
        return ["REVIEW_NOT_AN_OBJECT"], {"recorded": False}
    schema = review.get("schema")
    if schema is not None and schema != REVIEW_SCHEMA:
        blockers.append(f"REVIEW_SCHEMA_UNSUPPORTED:{schema}")

    reviewer = review.get("reviewer")
    if not isinstance(reviewer, str) or not reviewer.strip():
        blockers.append("REVIEW_REVIEWER_MISSING")

    declared = review.get("corpus_digest")
    if declared != digest:
        blockers.append("REVIEW_CORPUS_MISMATCH")
    if sample.get("corpus_digest") != digest:
        blockers.append("SAMPLE_CORPUS_MISMATCH")
    if sample.get("evidence_digest") != evidence_digest:
        blockers.append("SAMPLE_EVIDENCE_MISMATCH")
    if review.get("evidence_digest") != evidence_digest:
        blockers.append("REVIEW_EVIDENCE_MISMATCH")

    verdicts = review.get("verdicts")
    if not isinstance(verdicts, dict):
        blockers.append("REVIEW_VERDICTS_MISSING")
        verdicts = {}

    expected = [item["source"] for item in sample.get("items", [])]
    counts: Counter[str] = Counter()
    missing: list[str] = []
    rejected: list[str] = []
    unknown: list[str] = []
    for source in expected:
        entry = verdicts.get(source)
        verdict = entry.get("verdict") if isinstance(entry, dict) else entry
        if not isinstance(verdict, str) or not verdict.strip():
            missing.append(source)
            continue
        lowered = verdict.strip().lower()
        counts[lowered] += 1
        if lowered in REJECT_VERDICTS:
            rejected.append(source)
        elif lowered not in ACCEPT_VERDICTS:
            unknown.append(source)
    extra = sorted(set(verdicts) - set(expected))

    if missing:
        blockers.append(
            f"REVIEW_INCOMPLETE:{len(missing)}/{len(expected)} sampled records unreviewed"
        )
    if unknown:
        blockers.append(f"REVIEW_VERDICT_UNRECOGNIZED:{len(unknown)}")
    if rejected:
        blockers.append(f"REVIEW_REJECTED:{len(rejected)}")

    summary = {
        "recorded": True,
        "reviewer": reviewer if isinstance(reviewer, str) else None,
        "reviewed_at": review.get("reviewed_at"),
        "corpus_digest": declared,
        "evidence_digest": review.get("evidence_digest"),
        "sampled_records": len(expected),
        "verdict_counts": dict(sorted(counts.items())),
        "missing": missing[:20],
        "rejected": rejected[:20],
        "unrecognized": unknown[:20],
        "not_in_sample": extra[:20],
    }
    return blockers, summary


# ---------------------------------------------------------------------------
# gates
# ---------------------------------------------------------------------------


def _run_tool(script: Path, run_dir: Path, *options: str) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(script), *options, str(run_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _findings(stderr: str, limit: int = 10) -> list[str]:
    return [line for line in stderr.splitlines() if line.strip()][:limit]


def _reward_field_count(value: Any) -> int:
    if isinstance(value, dict):
        count = 0
        for key, child in value.items():
            if key == curate_rewards.ANNOTATION_FIELD:
                continue
            if key in curate_rewards.REWARD_KEYS:
                count += 1
            count += _reward_field_count(child)
        return count
    if isinstance(value, list):
        return sum(_reward_field_count(item) for item in value)
    return 0


def _reward_ontology_gate(cleaned: Path) -> dict[str, Any]:
    reward_bearing = 0
    annotated = 0
    missing: list[str] = []
    invalid: list[dict[str, str]] = []
    comparability: Counter[str] = Counter()

    for relative, line, record in iter_records(cleaned):
        if not isinstance(record, dict):
            continue
        reward_count = _reward_field_count(record)
        if not reward_count:
            continue
        reward_bearing += 1
        where = f"{relative}:{line}"
        annotation = record.get(curate_rewards.ANNOTATION_FIELD)
        if annotation is None:
            missing.append(where)
            continue
        annotated += 1
        try:
            curate_rewards.validate_ontology_document(annotation)
            if annotation.get("source_reward_count") != reward_count:
                raise curate_rewards.RewardOntologyError(
                    "source_reward_count does not match record reward fields"
                )
        except curate_rewards.RewardOntologyError as exc:
            invalid.append({"source": where, "error": str(exc)})
            continue
        comparability[str(annotation["comparability"])] += 1

    return {
        "tool": "curate_rewards.validate_ontology_document",
        "passed": not missing and not invalid,
        "reward_bearing_records": reward_bearing,
        "annotated_records": annotated,
        "missing_annotations": len(missing),
        "invalid_annotations": len(invalid),
        "comparability": dict(sorted(comparability.items())),
        "examples": [
            *(
                {"source": source, "error": "reward_training annotation missing"}
                for source in missing[:5]
            ),
            *invalid[:5],
        ][:5],
    }


def _pointer_value(document: Any, pointer: Any) -> Any:
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise curate_rewards.RewardOntologyError(f"invalid JSON pointer: {pointer!r}")
    value = document
    for raw_token in pointer[1:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            try:
                value = value[int(token)]
            except (ValueError, IndexError) as exc:
                raise curate_rewards.RewardOntologyError(
                    f"sidecar pointer does not resolve: {pointer}"
                ) from exc
        elif isinstance(value, dict) and token in value:
            value = value[token]
        else:
            raise curate_rewards.RewardOntologyError(f"sidecar pointer does not resolve: {pointer}")
    return value


def _walk_reward_values(value: Any, path: tuple[str | int, ...] = ()) -> Iterable[tuple[str, Any]]:
    """Yield reward scopes from retained output, independent of sidecar claims."""
    if isinstance(value, dict):
        for key, child in value.items():
            if key == curate_rewards.ANNOTATION_FIELD:
                continue
            child_path = (*path, key)
            if key in curate_rewards.REWARD_KEYS:
                yield _json_pointer(child_path), child
            yield from _walk_reward_values(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_reward_values(child, (*path, index))


def _reward_calibration_catalog(
    prepared_lanes: Sequence[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    catalogs = [
        dict(artifact.get("_catalog") or {})
        for lane in prepared_lanes
        for artifact in lane.get("artifacts", [])
        if artifact.get("kind") == REWARD_CALIBRATION_KIND
    ]
    if len(catalogs) > 1:
        raise GateError("more than one calibration artifact across all lanes")
    return catalogs[0] if catalogs else {}


def _authenticated_record_calibration(
    source_record: dict[str, Any] | None,
    sidecar: dict[str, Any],
    catalog: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    claimed = sidecar.get("calibration")
    source = sidecar.get("source") if isinstance(sidecar.get("source"), dict) else {}
    sidecar_record_id = source.get("record_id")
    authenticated_id = (
        curate_rewards.canonical_source_record_id(source_record)
        if source_record is not None
        else None
    )
    if (
        source_record is not None
        and sidecar_record_id is not None
        and (
            authenticated_id is None
            or not isinstance(sidecar_record_id, str)
            or curate_rewards.catalog_record_key(authenticated_id)
            != curate_rewards.catalog_record_key(sidecar_record_id)
        )
    ):
        raise curate_rewards.RewardOntologyError(
            "sidecar calibration source identity does not match the authenticated record"
        )
    lookup_id = authenticated_id or sidecar_record_id
    expected = (
        catalog.get(curate_rewards.catalog_record_key(lookup_id))
        if isinstance(lookup_id, str) and lookup_id.strip()
        else None
    )
    if claimed is None:
        if expected is not None:
            raise curate_rewards.RewardOntologyError(
                "sidecar omits calibration evidence present in the migration artifact"
            )
        return None
    normalized_claimed = curate_rewards.normalize_calibration(claimed)
    if expected is None:
        raise curate_rewards.RewardOntologyError(
            "external calibration has no matching record in the migration artifact"
        )
    normalized_expected = curate_rewards.normalize_calibration(expected)
    if normalized_claimed["source_unit_usd"] != normalized_expected["source_unit_usd"]:
        raise curate_rewards.RewardOntologyError(
            "sidecar calibration does not match the migration artifact for its source record"
        )
    return expected


def _derived_reward_contract(
    record: dict[str, Any],
    sidecar: dict[str, Any],
    calibration_catalog: dict[str, dict[str, Any]],
    source_record: dict[str, Any] | None,
) -> dict[str, Any]:
    """Recompute ontology semantics from row values and authenticated evidence."""
    calibration = _authenticated_record_calibration(
        source_record,
        sidecar,
        calibration_catalog,
    )
    output_record = copy.deepcopy(record)
    output_record.pop(curate_rewards.ANNOTATION_FIELD, None)
    reward_items = sorted(_walk_reward_values(output_record), key=lambda item: item[0])
    source_rewards = [
        {
            "json_pointer": pointer,
            "value_sha256": "sha256:" + record_sha256(value),
            "value": copy.deepcopy(value),
        }
        for pointer, value in reward_items
    ]
    arithmetic = [
        curate_rewards.assess_arithmetic(value, pointer) for pointer, value in reward_items
    ]
    comparability, reason_codes, payload = curate_rewards.classify_source_rewards(
        source_rewards,
        arithmetic,
        calibration,
    )
    return {
        "source_rewards": source_rewards,
        "arithmetic": arithmetic,
        "classification": {
            "comparability": comparability,
            "reason_codes": reason_codes,
        },
        "payload": payload,
    }


def _authenticate_reward_semantics(
    record: dict[str, Any],
    annotation: dict[str, Any],
    sidecar: dict[str, Any],
    calibration_catalog: dict[str, dict[str, Any]],
    source_record: dict[str, Any] | None,
) -> None:
    derived = _derived_reward_contract(
        record,
        sidecar,
        calibration_catalog,
        source_record,
    )
    if sidecar.get("source_rewards") != derived["source_rewards"]:
        raise curate_rewards.RewardOntologyError(
            "source_rewards do not match independently enumerated reward values"
        )
    if sidecar.get("arithmetic") != derived["arithmetic"]:
        raise curate_rewards.RewardOntologyError(
            "sidecar arithmetic does not match independent recomputation"
        )
    if sidecar.get("classification") != derived["classification"]:
        raise curate_rewards.RewardOntologyError(
            "sidecar classification does not match independent derivation"
        )
    classification = derived["classification"]
    if (
        annotation.get("comparability") != classification["comparability"]
        or annotation.get("reason_codes") != classification["reason_codes"]
    ):
        raise curate_rewards.RewardOntologyError(
            "record classification does not match independent derivation"
        )
    if annotation.get("source_reward_count") != len(derived["source_rewards"]):
        raise curate_rewards.RewardOntologyError(
            "record annotation reward count mismatches independent enumeration"
        )
    comparability = classification["comparability"]
    if comparability == curate_rewards.MAGNITUDE_COMPARABLE:
        if annotation.get("magnitude") != derived["payload"] or "order" in annotation:
            raise curate_rewards.RewardOntologyError(
                "canonical magnitude or calibration does not match independent derivation"
            )
    elif comparability == curate_rewards.SIGN_ORDER_ONLY:
        if annotation.get("order") != derived["payload"] or "magnitude" in annotation:
            raise curate_rewards.RewardOntologyError(
                "preference order does not match independent derivation"
            )
    elif "magnitude" in annotation or "order" in annotation:
        raise curate_rewards.RewardOntologyError(
            "excluded reward class must not carry magnitude or order claims"
        )


def _reward_sidecar_gate(
    cleaned: Path,
    bindings: Sequence[dict[str, Any]],
    prepared_lanes: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    sidecars: dict[str, dict[str, Any]] = {}
    sidecar_root = cleaned / GOVERNANCE_DIRNAME / REWARD_SIDECAR_DIRNAME
    artifact_paths = (
        [path for path in sorted(sidecar_root.rglob("*")) if path.is_file()]
        if sidecar_root.is_dir()
        else []
    )
    invalid: list[dict[str, str]] = []
    sidecar_sources: dict[tuple[str, int], str] = {}
    for path in artifact_paths:
        try:
            documents = _load_reward_sidecars(path)
        except GateError as exc:
            invalid.append({"source": path.relative_to(cleaned).as_posix(), "error": str(exc)})
            continue
        for document in documents:
            sidecar_id = document["sidecar_id"]
            if sidecar_id in sidecars:
                invalid.append(
                    {
                        "source": path.relative_to(cleaned).as_posix(),
                        "error": f"duplicate sidecar_id {sidecar_id}",
                    }
                )
            else:
                sidecars[sidecar_id] = document
                source = document.get("source")
                try:
                    if not isinstance(source, dict):
                        raise GateError("sidecar source must be an object")
                    source_key = (
                        _logical_source_path(source.get("path"), "sidecar source.path"),
                        source.get("line"),
                    )
                    if (
                        not isinstance(source_key[1], int)
                        or isinstance(source_key[1], bool)
                        or source_key[1] < 1
                    ):
                        raise GateError("sidecar source.line must be a positive integer")
                    if source_key in sidecar_sources:
                        raise GateError(
                            f"sidecar source identity duplicates {sidecar_sources[source_key]}"
                        )
                    sidecar_sources[source_key] = sidecar_id
                except GateError as exc:
                    invalid.append(
                        {"source": path.relative_to(cleaned).as_posix(), "error": str(exc)}
                    )

    linked = 0
    missing: list[str] = []
    used_sidecars: dict[str, str] = {}
    calibration_catalog = _reward_calibration_catalog(prepared_lanes)
    binding_by_output = {
        (binding["output_path"], binding["output_line"]): binding for binding in bindings
    }
    final_source_keys = {(binding["source_path"], binding["source_line"]) for binding in bindings}
    terminal_source_keys: set[tuple[str, int]] = set()
    known_source_keys: set[tuple[str, int]] = set()
    known_source_record_hashes: dict[tuple[str, int], str] = {}
    source_records_by_key: dict[tuple[str, int], Any] = {}
    for lane in prepared_lanes:
        for entry in lane["entries"]:
            source_key = entry["_source_key"]
            known_source_keys.add(source_key)
            action = str(entry.get("action") or "").strip().lower()
            if action in EXCLUSION_ACTIONS | QUARANTINE_ACTIONS:
                terminal_source_keys.add(source_key)
            source_record = entry.get("_source_record")
            if source_record is not None:
                known_source_record_hashes[source_key] = record_sha256(source_record)
                source_records_by_key[source_key] = source_record
    for relative, line, record in iter_records(cleaned):
        if not isinstance(record, dict):
            continue
        annotation = record.get(curate_rewards.ANNOTATION_FIELD)
        if not isinstance(annotation, dict):
            continue
        where = f"{relative}:{line}"
        sidecar_id = annotation.get("source_sidecar_id")
        sidecar = sidecars.get(sidecar_id)
        if sidecar is None:
            missing.append(where)
            continue
        try:
            curate_rewards.validate_ontology_document(annotation)
            binding = binding_by_output.get((relative, line))
            if binding is None:
                raise curate_rewards.RewardOntologyError(
                    "reward annotation has no authenticated final-output binding"
                )
            source = sidecar.get("source")
            if not isinstance(source, dict):
                raise curate_rewards.RewardOntologyError("sidecar source must be an object")
            sidecar_source_path = _logical_source_path(
                source.get("path"), f"{where} sidecar source.path"
            )
            sidecar_source_line = source.get("line")
            if (
                sidecar_source_path != binding["source_path"]
                or sidecar_source_line != binding["source_line"]
            ):
                raise curate_rewards.RewardOntologyError(
                    "sidecar source identity mismatches final record binding"
                )
            source_record_sha256 = _normalized_sha256(
                source.get("record_sha256"), f"{where} sidecar source.record_sha256"
            )
            if source_record_sha256 != binding["source_record_sha256"]:
                raise curate_rewards.RewardOntologyError(
                    "sidecar source record digest mismatches final record binding"
                )
            first_use = used_sidecars.get(sidecar_id)
            if first_use is not None:
                raise curate_rewards.RewardOntologyError(
                    f"sidecar is linked by more than one final record (first {first_use})"
                )
            source_key = (binding["source_path"], binding["source_line"])
            source_record = source_records_by_key.get(source_key)
            _authenticate_reward_semantics(
                record,
                annotation,
                sidecar,
                calibration_catalog,
                source_record if isinstance(source_record, dict) else None,
            )
            for reward in sidecar["source_rewards"]:
                current = _pointer_value(record, reward.get("json_pointer"))
                expected_hash = _normalized_sha256(
                    reward.get("value_sha256"), f"{where} sidecar reward value_sha256"
                )
                if record_sha256(reward.get("value")) != expected_hash:
                    raise curate_rewards.RewardOntologyError(
                        "source reward sidecar value hash mismatch"
                    )
                if record_sha256(current) != expected_hash:
                    raise curate_rewards.RewardOntologyError(
                        f"record reward differs from sidecar at {reward.get('json_pointer')}"
                    )
                if isinstance(source_record, dict):
                    source_value = _pointer_value(source_record, reward.get("json_pointer"))
                    if record_sha256(source_value) != record_sha256(reward.get("value")):
                        raise curate_rewards.RewardOntologyError(
                            f"sidecar reward does not match authenticated source at {reward.get('json_pointer')}"
                        )
        except (curate_rewards.RewardOntologyError, GateError) as exc:
            invalid.append({"source": where, "error": str(exc)})
            continue
        used_sidecars[sidecar_id] = where
        linked += 1

    orphan_ids = sorted(set(sidecars) - set(used_sidecars))
    terminal_sidecars = 0
    for sidecar_id in orphan_ids:
        sidecar = sidecars[sidecar_id]
        source = sidecar.get("source")
        try:
            if not isinstance(source, dict):
                raise GateError("sidecar source must be an object")
            source_key = (
                _logical_source_path(source.get("path"), "sidecar source.path"),
                source.get("line"),
            )
            if source_key not in known_source_keys:
                raise GateError("orphan sidecar source is absent from lane evidence")
            if source_key in final_source_keys or source_key not in terminal_source_keys:
                raise GateError("reward sidecar has no bound final or terminal source record")
            expected_source_record_hash = known_source_record_hashes.get(source_key)
            if (
                expected_source_record_hash is not None
                and _normalized_sha256(source.get("record_sha256"), "sidecar source.record_sha256")
                != expected_source_record_hash
            ):
                raise GateError("terminal sidecar source record digest mismatches source evidence")
            terminal_sidecars += 1
        except GateError as exc:
            invalid.append({"source": sidecar_id, "error": str(exc)})

    return {
        "tool": "curate_rewards reward-source sidecar verifier",
        "passed": not missing and not invalid,
        "artifact_files": len(artifact_paths),
        "sidecars": len(sidecars),
        "linked_records": linked,
        "missing_sidecars": len(missing),
        "orphan_sidecars": len(orphan_ids),
        "terminal_sidecars": terminal_sidecars,
        "invalid_links": len(invalid),
        "examples": [
            *(
                {"source": source, "error": "source_sidecar_id does not resolve"}
                for source in missing[:5]
            ),
            *invalid[:5],
        ][:5],
    }


def run_gates(
    cleaned: Path,
    *,
    record_bindings: Any,
    prepared_lanes: Sequence[dict[str, Any]],
    lane_manifests: dict[str, Any],
) -> dict[str, Any]:
    """Structural, deep-invariant, and strict corpus gates on one destination."""
    cleaned = Path(cleaned).resolve()
    if not cleaned.is_dir():
        raise GateError(f"not a directory: {cleaned}")
    if not jsonl_paths(cleaned):
        raise GateError(f"cleaned destination holds no *.jsonl: {cleaned}")

    blockers: list[str] = []
    gates: dict[str, Any] = {}

    output_evidence, records_by_source, normalized_bindings = _output_evidence_gate(
        cleaned,
        record_bindings,
        prepared_lanes,
    )
    gates["output_evidence"] = output_evidence
    if not output_evidence["passed"]:
        blockers.append(
            f"OUTPUT_EVIDENCE_AUTHENTICATION:{output_evidence['invalid_bindings']} invalid"
        )

    identity_mappings = _identity_mapping_gate(
        lane_manifests["identity_mappings"],
        records_by_source,
    )
    gates["identity_mappings"] = identity_mappings
    if not identity_mappings["passed"]:
        blockers.append(
            f"IDENTITY_MAPPING_AUTHENTICATION:{identity_mappings['invalid_mappings']} invalid"
        )

    code, _out, err = _run_tool(VALIDATOR, cleaned)
    gates["structural_validator"] = {
        "tool": "validate_run.py",
        "exit": code,
        "passed": code == 0,
        "findings": _findings(err),
    }
    if code:
        blockers.append(f"STRUCTURAL_VALIDATOR_FAILED:exit {code}")

    code, _out, err = _run_tool(CHECKER, cleaned, "--strict")
    gates["record_invariants"] = {
        "tool": "check_records.py --strict",
        "exit": code,
        "passed": code == 0,
        "findings": _findings(err),
    }
    if code:
        blockers.append(f"RECORD_INVARIANTS_FAILED:exit {code}")

    report = training_audit.audit_run(cleaned)
    gates["training_audit"] = {
        "tool": "training_audit.py --strict",
        "passed": bool(report["training_ready"]),
        "blockers": list(report["blockers"]),
    }
    if not report["training_ready"]:
        blockers.append(f"TRAINING_NOT_READY:{len(report['blockers'])} audit blockers")

    exact_duplicates = report.get("exact_duplicates") or []
    gates["exact_duplicates"] = {
        "passed": not exact_duplicates,
        "count": len(exact_duplicates),
        "examples": exact_duplicates[:5],
    }
    if exact_duplicates:
        blockers.append(f"EXACT_DUPLICATES:{len(exact_duplicates)}")

    identity = report.get("identity") or {}
    collisions = identity.get("duplicates") or []
    gates["canonical_id_collisions"] = {
        "passed": not collisions,
        "count": len(collisions),
        "examples": collisions[:5],
    }
    if collisions:
        blockers.append(f"CANONICAL_ID_COLLISIONS:{len(collisions)}")

    missing_ids = identity.get("missing_top_level", 0)
    gates["canonical_id_coverage"] = {
        "passed": not missing_ids,
        "coverage_pct": identity.get("coverage_pct", 0),
        "missing_top_level": missing_ids,
        "examples": (identity.get("missing_examples") or [])[:5],
    }
    if missing_ids:
        blockers.append(f"CANONICAL_ID_COVERAGE:{missing_ids} records lack a top-level id")

    reward_gate = _reward_ontology_gate(cleaned)
    gates["reward_ontology"] = reward_gate
    if not reward_gate["passed"]:
        blockers.append(
            "REWARD_ONTOLOGY_COVERAGE:"
            f"{reward_gate['missing_annotations']} missing, "
            f"{reward_gate['invalid_annotations']} invalid"
        )

    reward_sidecars = _reward_sidecar_gate(cleaned, normalized_bindings, prepared_lanes)
    gates["reward_sidecars"] = reward_sidecars
    if not reward_sidecars["passed"]:
        blockers.append(
            "REWARD_SIDECAR_AUTHENTICATION:"
            f"{reward_sidecars['missing_sidecars']} missing, "
            f"{reward_sidecars['invalid_links']} invalid"
        )

    return {
        "gates": gates,
        "blockers": blockers,
        "audit": report,
        "training_ready": not blockers,
    }


def _corpus_counts(report: dict[str, Any]) -> dict[str, Any]:
    totals = report.get("totals") or {}
    factories = report.get("factories") or {}
    return {
        "files": totals.get("files", 0),
        "records": totals.get("records", 0),
        "bytes": totals.get("bytes", 0),
        "by_kind": dict(totals.get("by_kind") or {}),
        "by_factory": {
            name: bucket.get("records", 0) for name, bucket in sorted(factories.items())
        },
    }


# ---------------------------------------------------------------------------
# manifest
# ---------------------------------------------------------------------------


def build_manifest(
    *,
    plan: dict[str, Any],
    composition: dict[str, Any],
    lane_manifests: dict[str, Any],
    gate_result: dict[str, Any],
    sample: dict[str, Any],
    lane_evidence: Sequence[dict[str, Any]],
    governance_outputs: Sequence[dict[str, Any]],
    review: dict[str, Any] | None,
    blockers: Sequence[str],
) -> dict[str, Any]:
    report = gate_result["audit"]
    counts = _corpus_counts(report)
    counts["lane_actions"] = lane_manifests["actions_by_lane"]
    counts["exclusions"] = len(lane_manifests["exclusions"])
    counts["quarantines"] = len(lane_manifests["quarantines"])
    counts["repairs"] = len(lane_manifests["repairs"])
    counts["identity_mappings"] = len(lane_manifests["identity_mappings"])
    counts["sampled_for_review"] = sample["sampled_records"]
    counts["review_strata"] = sample["strata_count"]

    return {
        "schema": MANIFEST_SCHEMA,
        "generated_by": f"{TOOL_NAME}/{TOOL_VERSION}",
        "plan": {
            "path": str(plan["plan_path"]),
            "sha256": plan["plan_sha256"],
            "source_run": plan["source_run"],
        },
        "cleaned_dir": str(composition["destination"]),
        "corpus_digest": sample["corpus_digest"],
        "composition_order": composition["composition_order"],
        "transform_versions": plan["transform_versions"],
        "counts": counts,
        "inputs": composition["inputs"],
        "outputs": composition["outputs"],
        "record_bindings": composition["record_bindings"],
        "governance_outputs": list(governance_outputs),
        "supersessions": composition["supersessions"],
        "lane_evidence": list(lane_evidence),
        "exclusions": lane_manifests["exclusions"],
        "quarantines": lane_manifests["quarantines"],
        "repairs": lane_manifests["repairs"],
        "identity_mappings": lane_manifests["identity_mappings"],
        "review_candidates": lane_manifests["review_candidates"],
        "review_sampling": {
            "per_stratum": sample["per_stratum"],
            "sample_sha256": None,
        },
        "evidence_digest": None,
        "exclusion_reason_codes": lane_manifests["reason_codes"],
        "lanes_without_record_manifest": lane_manifests["lanes_without_manifest"],
        "gates": gate_result["gates"],
        "review": review if review is not None else {"recorded": False},
        "blockers": list(blockers),
        "training_ready": gate_result["training_ready"],
        "promotion": None,
    }


def manifest_evidence_digest(manifest: dict[str, Any]) -> str:
    """Hash the immutable integration manifest, excluding its self-reference."""
    payload = copy.deepcopy(manifest)
    payload.pop("evidence_digest", None)
    for mutable_key in ("review", "blockers", "promotion"):
        payload.pop(mutable_key, None)
    sampling = payload.get("review_sampling")
    if isinstance(sampling, dict):
        sampling.pop("sample_sha256", None)
    return "sha256:" + record_sha256(payload)


# ---------------------------------------------------------------------------
# subcommands
# ---------------------------------------------------------------------------


def cmd_integrate(args: argparse.Namespace) -> int:
    if args.per_stratum < 1:
        raise GateError("--per-stratum must be at least 1")
    plan = load_plan(Path(args.plan))
    declared_destination = Path(args.cleaned_out)
    if declared_destination.is_symlink():
        _assert_new_destination(declared_destination, "cleaned destination")
    destination = declared_destination.resolve(strict=False)
    _assert_disjoint_trees(
        plan["source_run_dir"],
        destination,
        source_label="source_run",
        destination_label="cleaned destination",
    )
    destination = _assert_new_destination(
        declared_destination,
        "cleaned destination",
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage_root = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.staging-", dir=destination.parent)
    )
    staged = stage_root / "tree"
    try:
        prepared_lanes = prepare_lanes(plan)
        composition = compose(
            plan,
            staged,
            logical_destination=destination,
            prepared_lanes=prepared_lanes,
        )
        lane_evidence, governance_outputs = copy_lane_evidence(prepared_lanes, staged)
        retained_source_keys = {
            (binding["source_path"], binding["source_line"])
            for binding in composition["record_bindings"]
        }
        lane_manifests = collect_lane_manifests(prepared_lanes, retained_source_keys)
        gate_result = run_gates(
            staged,
            record_bindings=composition["record_bindings"],
            prepared_lanes=prepared_lanes,
            lane_manifests=lane_manifests,
        )
        sample = build_sample(staged, args.per_stratum, lane_manifests["review_candidates"])
        sample["cleaned_dir"] = str(destination)

        blockers = list(gate_result["blockers"])
        blockers.append("REVIEW_NOT_RECORDED")

        manifest = build_manifest(
            plan=plan,
            composition=composition,
            lane_manifests=lane_manifests,
            gate_result=gate_result,
            sample=sample,
            lane_evidence=lane_evidence,
            governance_outputs=governance_outputs,
            review=None,
            blockers=blockers,
        )
        evidence_digest = manifest_evidence_digest(manifest)
        manifest["evidence_digest"] = evidence_digest
        sample["evidence_digest"] = evidence_digest
        manifest["review_sampling"]["sample_sha256"] = sha256_hex(
            training_audit.canonical_blob(sample).encode("utf-8")
        )
        _write_json(staged / MANIFEST_FILENAME, manifest)
        _write_json(staged / SAMPLE_FILENAME, sample)
        _write_json(staged / REVIEW_FILENAME, review_template(sample))

        # Publish only a complete tree. A copy, manifest, gate, or sidecar
        # failure leaves the requested destination absent and retryable.
        expected_tree = _tree_snapshot(staged)
        if corpus_digest(staged) != sample["corpus_digest"]:
            raise GateError("staged corpus changed after integration validation")
        _rename_noreplace(staged, destination, "cleaned destination", expected_tree)
    finally:
        shutil.rmtree(stage_root, ignore_errors=True)

    summary = {
        "cleaned_out": str(destination),
        "corpus_digest": sample["corpus_digest"],
        "training_ready": gate_result["training_ready"],
        "gate_blockers": gate_result["blockers"],
        "counts": manifest["counts"],
        "review_sample": str(destination / SAMPLE_FILENAME),
        "review_template": str(destination / REVIEW_FILENAME),
        "manifest": str(destination / MANIFEST_FILENAME),
        "next_step": (
            "record a verdict for every sampled record, then run "
            f"'{TOOL_NAME}.py promote --cleaned {destination} --review <file> "
            "--curated-out <new path>'"
        ),
    }
    print(json.dumps(summary, indent=2))
    return 0 if gate_result["training_ready"] else 1


def _promotion_outputs(curated: Path) -> list[dict[str, Any]]:
    entries = []
    for path in sorted(curated.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(curated).as_posix()
        if relative in {MANIFEST_FILENAME, SAMPLE_FILENAME, REVIEW_FILENAME}:
            continue
        entries.append(
            {
                "path": relative,
                "sha256": file_sha256(path),
                "bytes": path.stat().st_size,
            }
        )
    return entries


def _snapshot_bytes(source: Path, root: Path, label: str) -> bytes:
    if source.is_symlink() or not source.is_file():
        raise GateError(f"{label} must be a regular, non-symlink file: {source}")
    _assert_no_symlink(root, source, label)
    try:
        return source.read_bytes()
    except OSError as exc:
        raise GateError(f"cannot snapshot {label} {source}: {exc}") from exc


def _snapshot_reviewed_tree(
    cleaned: Path,
    review_path: Path,
    destination: Path,
) -> dict[str, Any]:
    """Capture once, then validate and publish only these staged bytes.

    No source file is read again after this function returns.  Cross-file
    digests and all gates are evaluated on ``destination``, which is renamed
    directly into place after successful validation.
    """
    corpus_paths = jsonl_paths(cleaned)
    if not corpus_paths:
        raise GateError(f"no JSONL corpus files under {cleaned}")
    governance = cleaned / GOVERNANCE_DIRNAME
    if not governance.is_dir():
        raise GateError(f"cleaned corpus is missing {GOVERNANCE_DIRNAME} evidence")
    governance_paths = [path for path in sorted(governance.rglob("*")) if path.is_file()]
    control_paths = [cleaned / MANIFEST_FILENAME, cleaned / SAMPLE_FILENAME]
    for control in control_paths:
        if not control.is_file():
            raise GateError(f"cleaned corpus is missing promotion control file: {control}")

    destination.mkdir(parents=True)
    entries: list[dict[str, Any]] = []
    records = 0
    for source in [*corpus_paths, *governance_paths, *control_paths]:
        relative = source.relative_to(cleaned)
        payload = _snapshot_bytes(source, cleaned, "cleaned promotion input")
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        entry = {
            "path": relative.as_posix(),
            "sha256": sha256_hex(payload),
            "bytes": len(payload),
        }
        entries.append(entry)
        if source in corpus_paths:
            try:
                text = payload.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise GateError(f"cannot snapshot invalid UTF-8 JSONL {source}: {exc}") from exc
            records += sum(1 for line in _lf_lines(text) if line.strip())

    review_payload = _snapshot_bytes(review_path, review_path.parent, "review evidence")
    (destination / REVIEW_FILENAME).write_bytes(review_payload)
    review_entry = {
        "path": REVIEW_FILENAME,
        "source_path": str(review_path),
        "sha256": sha256_hex(review_payload),
        "bytes": len(review_payload),
    }
    entries.append({key: value for key, value in review_entry.items() if key != "source_path"})

    by_path = {entry["path"]: entry for entry in entries}
    governance_entries = [
        entry for entry in entries if Path(entry["path"]).parts[0] == GOVERNANCE_DIRNAME
    ]
    return {
        "files": len(corpus_paths),
        "records": records,
        "resorted": 0,
        "governance_files": len(governance_paths),
        "inputs": entries,
        "review": review_entry,
        "integration_manifest": by_path[MANIFEST_FILENAME],
        "review_sample": by_path[SAMPLE_FILENAME],
        "governance": governance_entries,
    }


def _assert_disjoint_trees(
    source: Path,
    destination: Path,
    *,
    source_label: str = "cleaned",
    destination_label: str = "curated",
) -> None:
    source = source.resolve(strict=False)
    destination = destination.resolve(strict=False)
    if source == destination or source in destination.parents or destination in source.parents:
        raise GateError(
            f"{source_label} and {destination_label} must be disjoint after symlink "
            f"resolution: {source_label}={source}, {destination_label}={destination}"
        )


def cmd_promote(args: argparse.Namespace) -> int:
    cleaned = Path(args.cleaned).resolve()
    curated = _assert_new_destination(
        Path(args.curated_out),
        "curated destination",
    )
    if not cleaned.is_dir():
        raise GateError(f"not a directory: {cleaned}")
    _assert_disjoint_trees(cleaned, curated)
    review_path = Path(args.review).resolve()
    if not review_path.is_file():
        raise GateError(f"review evidence is missing: {review_path}")
    curated.parent.mkdir(parents=True, exist_ok=True)
    stage_root = Path(tempfile.mkdtemp(prefix=f".{curated.name}.staging-", dir=curated.parent))
    staged = stage_root / "tree"
    try:
        # Capture the corpus, governance evidence, integration controls, and
        # supplied review exactly once.  Everything below reads only ``staged``.
        promotion = _snapshot_reviewed_tree(cleaned, review_path, staged)
        manifest_path = staged / MANIFEST_FILENAME
        sample_path = staged / SAMPLE_FILENAME
        staged_review_path = staged / REVIEW_FILENAME
        manifest = _load_json(manifest_path)
        if not isinstance(manifest, dict):
            raise GateError(f"{manifest_path}: manifest must be a JSON object")
        sample = _load_json(sample_path)
        if not isinstance(sample, dict) or not isinstance(sample.get("items"), list):
            raise GateError(f"{sample_path}: review sample must be an object with an 'items' list")
        review = _load_json(staged_review_path)

        digest = corpus_digest(staged)
        evidence_digest = manifest.get("evidence_digest")
        if not isinstance(evidence_digest, str) or not evidence_digest.startswith("sha256:"):
            raise GateError(f"{manifest_path}: evidence_digest must be a SHA-256")
        _normalized_sha256(evidence_digest, f"{manifest_path}: evidence_digest")
        normalized_bindings = _normalize_record_bindings(manifest.get("record_bindings"))
        retained_source_keys = {
            (binding["source_path"], binding["source_line"]) for binding in normalized_bindings
        }
        source_record_sha256_by_key = {
            (binding["source_path"], binding["source_line"]): binding["source_record_sha256"]
            for binding in normalized_bindings
        }
        evidence_lanes, rebuilt_lane_manifests = verify_lane_evidence(
            staged,
            manifest,
            retained_source_keys,
            source_record_sha256_by_key,
        )
        gate_result = run_gates(
            staged,
            record_bindings=normalized_bindings,
            prepared_lanes=evidence_lanes,
            lane_manifests=rebuilt_lane_manifests,
        )
        sampling = manifest.get("review_sampling")
        if not isinstance(sampling, dict):
            raise GateError(f"{manifest_path}: review_sampling must be an object")
        per_stratum = sampling.get("per_stratum")
        if not isinstance(per_stratum, int) or isinstance(per_stratum, bool) or per_stratum < 1:
            raise GateError(f"{manifest_path}: review_sampling.per_stratum must be at least 1")
        expected_sample = build_sample(
            staged,
            per_stratum,
            rebuilt_lane_manifests["review_candidates"],
            evidence_digest=evidence_digest,
        )
        expected_sample["cleaned_dir"] = str(cleaned)
        review_blockers, review_summary = check_review(
            expected_sample,
            review,
            digest,
            evidence_digest,
        )
        if manifest_evidence_digest(manifest) != evidence_digest:
            review_blockers.append("INTEGRATION_EVIDENCE_MISMATCH")
        if manifest.get("cleaned_dir") != str(cleaned):
            review_blockers.append("CLEANED_DESTINATION_MISMATCH")
        evidence_sections = {
            "exclusions": rebuilt_lane_manifests["exclusions"],
            "quarantines": rebuilt_lane_manifests["quarantines"],
            "repairs": rebuilt_lane_manifests["repairs"],
            "identity_mappings": rebuilt_lane_manifests["identity_mappings"],
            "review_candidates": rebuilt_lane_manifests["review_candidates"],
            "exclusion_reason_codes": rebuilt_lane_manifests["reason_codes"],
            "lanes_without_record_manifest": [],
        }
        if any(manifest.get(key) != value for key, value in evidence_sections.items()):
            review_blockers.append("LANE_EVIDENCE_SUMMARY_MISMATCH")
        expected_sample_hash = sha256_hex(
            training_audit.canonical_blob(expected_sample).encode("utf-8")
        )
        if sampling.get("sample_sha256") != expected_sample_hash:
            review_blockers.append("SAMPLE_MANIFEST_MISMATCH")
        if sample.get("corpus_digest") != digest:
            review_blockers.append("SAMPLE_CORPUS_MISMATCH")
        if sample != expected_sample:
            review_blockers.append("SAMPLE_SELECTION_MISMATCH")

        blockers = list(dict.fromkeys([*gate_result["blockers"], *review_blockers]))
        if blockers:
            print(
                json.dumps(
                    {
                        "promoted": False,
                        "cleaned": str(cleaned),
                        "curated_out": str(curated),
                        "blockers": blockers,
                        "manifest": str(cleaned / MANIFEST_FILENAME),
                    },
                    indent=2,
                )
            )
            return 1

        final_manifest = copy.deepcopy(manifest)
        final_manifest["corpus_digest"] = digest
        final_manifest["gates"] = gate_result["gates"]
        counts = final_manifest.get("counts")
        if not isinstance(counts, dict):
            counts = {}
        counts.update(_corpus_counts(gate_result["audit"]))
        final_manifest["counts"] = counts
        review_summary["review_sha256"] = promotion["review"]["sha256"]
        final_manifest["review"] = review_summary
        final_manifest["training_ready"] = gate_result["training_ready"]
        final_manifest["blockers"] = []

        promoted_digest = corpus_digest(staged)
        if promoted_digest != digest:
            raise GateError("staged corpus changed after validation")
        promoted_outputs = _promotion_outputs(staged)
        governance_outputs = [
            entry
            for entry in promoted_outputs
            if Path(entry["path"]).parts[0] == GOVERNANCE_DIRNAME
        ]
        final_manifest["promotion"] = {
            "curated_dir": str(curated),
            "promoter": "pipelines/curate_gate.py immutable-staged-snapshot",
            "files": promotion["files"],
            "records": promotion["records"],
            "resorted": promotion["resorted"],
            "governance_files": promotion["governance_files"],
            "outputs": promoted_outputs,
            "corpus_digest": promoted_digest,
            "evidence_digest": evidence_digest,
            "integration_manifest_sha256": promotion["integration_manifest"]["sha256"],
            "review_sample_sha256": promotion["review_sample"]["sha256"],
            "review_sha256": promotion["review"]["sha256"],
            "governance_evidence_digest": "sha256:" + record_sha256(governance_outputs),
        }

        # The final manifest replaces its captured integration predecessor;
        # corpus, governance, sample, and review bytes are never recopied.
        _write_json(staged / MANIFEST_FILENAME, final_manifest)
        expected_tree = _tree_snapshot(staged)
        if file_sha256(staged / SAMPLE_FILENAME) != promotion["review_sample"]["sha256"]:
            raise GateError("staged review sample changed after validation")
        if file_sha256(staged / REVIEW_FILENAME) != promotion["review"]["sha256"]:
            raise GateError("staged review evidence changed after validation")
        if corpus_digest(staged) != promoted_digest:
            raise GateError("staged corpus changed after final promotion validation")
        if _promotion_outputs(staged) != promoted_outputs:
            raise GateError("staged promotion outputs changed after final validation")
        _rename_noreplace(staged, curated, "curated destination", expected_tree)
    finally:
        shutil.rmtree(stage_root, ignore_errors=True)

    print(
        json.dumps(
            {
                "promoted": True,
                "cleaned": str(cleaned),
                "curated_out": str(curated),
                "corpus_digest": final_manifest["promotion"]["corpus_digest"],
                "files": promotion["files"],
                "records": promotion["records"],
                "reviewer": review_summary.get("reviewer"),
                "manifest": str(curated / MANIFEST_FILENAME),
            },
            indent=2,
        )
    )
    return 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compose curation lanes into one new cleaned destination, gate it, "
            "and promote it to a new curated path."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    integrate = sub.add_parser(
        "integrate",
        help="compose lane outputs in plan order, gate them, record a review sample",
    )
    integrate.add_argument("--plan", required=True, help="integration plan JSON")
    integrate.add_argument(
        "--cleaned-out", required=True, help="brand-new cleaned destination (must not exist)"
    )
    integrate.add_argument(
        "--per-stratum",
        type=int,
        default=DEFAULT_PER_STRATUM,
        help=f"records sampled per stratum (default {DEFAULT_PER_STRATUM})",
    )
    integrate.set_defaults(handler=cmd_integrate)

    promote_cmd = sub.add_parser(
        "promote",
        help="re-gate a cleaned destination and promote it once the sample is reviewed",
    )
    promote_cmd.add_argument(
        "--cleaned", required=True, help="cleaned destination written by 'integrate'"
    )
    promote_cmd.add_argument("--review", required=True, help="reviewed verdict file")
    promote_cmd.add_argument(
        "--curated-out", required=True, help="brand-new curated destination (must not exist)"
    )
    promote_cmd.set_defaults(handler=cmd_promote)

    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return args.handler(args)
    except GateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
