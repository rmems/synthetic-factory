#!/usr/bin/env python3
"""Independent-arm gate for two-session preference generation.

``failure-as-fuel-preference-cascade`` generates its ``rejected`` and
``chosen`` arms in two isolated sessions (``docs/preference-isolation.md``).
Isolation buys nothing if the published pair still reads as one arm copied
and lightly edited, so every staged round must clear two invariants:

1. **Same-context purity** — ``chosen`` and ``rejected`` share canonically
   identical ``state`` and ``proposed_action``. This delegates to the
   canonical implementation in ``curate_preferences.context_is_pure``; it is
   re-checked here so one command gates a round.
2. **Independent arms** — the allowlisted machine-behavior surfaces
   (``executed_action``, ``future_outcome``, and ``spike_events``) must sit
   more than ``--min-distance`` apart and share at least one changed
   machine-observable leaf. Distance is ``1 - cosine_similarity`` over
   path-scoped term-frequency vectors over one reviewed observable projection;
   one-sided nested fields cannot add distance, and unordered lists are
   matched after exact multiset cancellation. This metric has its own
   fixture-calibrated floor; it is not presented as equivalent to an
   embedding model. Separate structural checks reject gate-label copies,
   narrative padding, and unknown top-level arm extensions.

The read-only gate requires each pair to declare
``meta.isolation == "two-session"``. Publication additionally requires a
reservation-bound orchestration assertion; record metadata alone is never
treated as proof of the protocol.

Read-only scan (exit 1 when any pair is blocked)::

    python3 pipelines/preference_arms.py scan <batch-or-dir> [--json]

Verify Session A's diagnosis-only handoff and persist the receipt that
publication requires::

    python3 pipelines/preference_arms.py verify-handoff <staging-dir> \
        --file diagnosis-01-rNN.md --file diagnosis-02-rNN.md \
        --write-receipt

``source`` may be one JSONL file or a directory scanned recursively for
``*.jsonl``. Records without preference-pair fields are counted and skipped.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from curate_preferences import canonical_json, context_is_pure  # noqa: E402,F401

# The gate is split across sibling modules so each states one responsibility.
# Everything the published surface exposes is re-exported here, so
# ``import preference_arms`` keeps resolving every name it always did.
from preference_arms_diagnosis import (  # noqa: E402,F401
    DIAGNOSIS_SECTIONS,
    HANDOFF_RECEIPT_VERSION,
    MAX_DIAGNOSIS_BYTES,
    MAX_DIAGNOSIS_COMPONENTS,
    MAX_DIAGNOSIS_DEPTH,
    MAX_DIAGNOSIS_LINE_CHARS,
    MAX_DIAGNOSIS_NARRATIVE_CHARS,
    MAX_DIAGNOSIS_NODES,
    _DIAGNOSIS_NAME_RE,
    _FACTORY_SLUG_RE,
    _STAGING_NAME_RE,
    _session_b_outputs,
    _strict_json_object,
    diagnosis_filenames,
    diagnosis_receipt_filename,
    validate_diagnosis_document,
)
from preference_arms_fs import (  # noqa: E402,F401
    _open_canonical_directory,
    _read_regular_artifact,
    _read_regular_artifact_from_directory,
    _require_open_directory_identity,
    _same_file_identity,
)
from preference_arms_observables import (  # noqa: E402,F401
    CONTRAST_FIELDS,
    DEFAULT_MIN_ARM_DISTANCE,
    LABEL_COPY_FIELDS,
    MACHINE_BOOLEAN_PATHS,
    MACHINE_IDENTIFIER_PATHS,
    MACHINE_NUMERIC_PATHS,
    MACHINE_OBSERVABLE_FIELDS,
    MAX_ALIGNMENT_LIST_ITEMS,
    MAX_ALIGNMENT_RESIDUAL_ITEMS,
    SPIKE_IDENTIFIER_KEYS,
    _common_arm_observable_leaves,
    _observable_deltas_from_leaves,
    _observable_terms,
    _validated_distance_floor,
    arm_distance,
    arm_terms,
    differs_only_by_gate_label,
    machine_observable_deltas,
)
from preference_arms_receipt import validate_diagnosis_handoff_receipt  # noqa: E402,F401
from preference_arms_report import ArmDecision, ArmScan, render_human  # noqa: E402,F401
from preference_arms_text import (  # noqa: E402,F401
    ListAlignmentError,
    PreferenceArmsError,
    cosine_similarity,
)

GATE_NAME = "independent-preference-arms"
GATE_VERSION = "1.6.0"


#: The only accepted ``meta.isolation`` value. Anything else is the
#: deprecated single-context generation path.
TWO_SESSION = "two-session"

#: The published arm contract. Unknown top-level extensions cannot be used as
#: lexical padding to manufacture distance.
ARM_FIELDS = frozenset(
    {
        "id",
        "goal",
        "state",
        "proposed_action",
        "safety_decision",
        "executed_action",
        "future_outcome",
        "reward_components",
        "spike_events",
        "provenance",
        "meta",
    }
)

#: Fields that carry measured behavioral contrast. Producer-authored safety
#: rationale is deliberately absent: prose length, padding, or homoglyphs may
#: not establish independence when the executed behavior did not change.
CONTEXT_FIELDS = ("state", "proposed_action")




REASON_MALFORMED = "PREFERENCE_PAIR_MALFORMED"
REASON_CONTEXT_DIVERGES = "PREFERENCE_CONTEXT_DIVERGES"
REASON_NEAR_VERBATIM = "PREFERENCE_ARMS_NEAR_VERBATIM"
REASON_CONTRAST_EMPTY = "PREFERENCE_ARM_CONTRAST_EMPTY"
REASON_ISOLATION_UNDECLARED = "PREFERENCE_ARMS_ISOLATION_UNDECLARED"
REASON_ISOLATION_CONFLICT = "PREFERENCE_ARMS_ISOLATION_CONFLICT"
REASON_SINGLE_SESSION = "PREFERENCE_ARMS_SINGLE_SESSION_PATH"
REASON_ISOLATION_UNTRUSTED = "PREFERENCE_ARMS_ISOLATION_UNTRUSTED"
REASON_LABEL_ONLY_COPY = "PREFERENCE_ARMS_LABEL_ONLY_COPY"
REASON_EXTENSION_FIELDS = "PREFERENCE_ARM_EXTENSION_FIELDS"
REASON_OBSERVABLES_IDENTICAL = "PREFERENCE_ARMS_OBSERVABLES_IDENTICAL"
REASON_LIST_ALIGNMENT = "PREFERENCE_ARM_LIST_ALIGNMENT_UNTRUSTED"
































































def _declared_isolation(
    record: dict[str, Any], chosen: dict[str, Any], rejected: dict[str, Any]
) -> tuple[str | None, bool]:
    """Return the pair's declared isolation and whether declarations conflict.

    The launcher stamps ``meta.isolation`` at assembly time; accept it on the
    record or on either arm, but never accept disagreeing declarations.
    """

    declared: list[str] = []
    for holder in (record, chosen, rejected):
        meta = holder.get("meta")
        if not isinstance(meta, dict):
            continue
        value = meta.get("isolation")
        if isinstance(value, str) and value.strip():
            declared.append(value.strip())
    if not declared:
        return None, False
    unique = sorted(set(declared))
    if len(unique) > 1:
        # Report the disagreement itself so the operator sees both claims.
        return "|".join(unique), True
    return unique[0], False


def check_pair(
    record: dict[str, Any],
    *,
    source_path: str,
    source_line: int,
    min_distance: float = DEFAULT_MIN_ARM_DISTANCE,
    require_isolation: bool = True,
    trusted_isolation: str | None = None,
    require_trusted_isolation: bool = False,
) -> ArmDecision:
    """Gate one preference record without mutating it."""

    min_distance = _validated_distance_floor(min_distance)

    record_id = record.get("id") if isinstance(record.get("id"), str) else None
    chosen = record.get("chosen")
    rejected = record.get("rejected")
    if not isinstance(chosen, dict) or not isinstance(rejected, dict):
        return ArmDecision(
            source_path=source_path,
            source_line=source_line,
            record_id=record_id,
            same_context=False,
            isolation=None,
            trusted_isolation=trusted_isolation,
            arm_distance=None,
            cosine_similarity=None,
            reason_codes=(REASON_MALFORMED,),
        )

    reasons: list[str] = []
    extension_fields = sorted((set(chosen) | set(rejected)) - ARM_FIELDS)
    if extension_fields:
        reasons.append(REASON_EXTENSION_FIELDS)
    same_context = context_is_pure(record)
    if not same_context:
        reasons.append(REASON_CONTEXT_DIVERGES)

    isolation, conflicting = _declared_isolation(record, chosen, rejected)
    if require_isolation:
        if isolation is None:
            reasons.append(REASON_ISOLATION_UNDECLARED)
        elif conflicting:
            reasons.append(REASON_ISOLATION_CONFLICT)
        elif isolation != TWO_SESSION:
            reasons.append(REASON_SINGLE_SESSION)
    if require_trusted_isolation and trusted_isolation != TWO_SESSION:
        reasons.append(REASON_ISOLATION_UNTRUSTED)

    try:
        observable_leaves = _common_arm_observable_leaves(chosen, rejected)
    except ListAlignmentError:
        observable_leaves = []
        reasons.append(REASON_LIST_ALIGNMENT)
    chosen_terms, rejected_terms = _observable_terms(observable_leaves)
    if not chosen_terms or not rejected_terms:
        reasons.append(REASON_CONTRAST_EMPTY)
    if differs_only_by_gate_label(chosen, rejected):
        reasons.append(REASON_LABEL_ONLY_COPY)
    if not _observable_deltas_from_leaves(observable_leaves):
        reasons.append(REASON_OBSERVABLES_IDENTICAL)
    similarity = cosine_similarity(chosen_terms, rejected_terms)
    distance = 1.0 - similarity
    if distance <= min_distance:
        reasons.append(REASON_NEAR_VERBATIM)

    return ArmDecision(
        source_path=source_path,
        source_line=source_line,
        record_id=record_id,
        same_context=same_context,
        isolation=isolation,
        trusted_isolation=trusted_isolation,
        arm_distance=round(distance, 6),
        cosine_similarity=round(similarity, 6),
        reason_codes=tuple(reasons),
    )


def _is_preference_candidate(record: Any) -> bool:
    return isinstance(record, dict) and any(
        key in record for key in ("chosen", "rejected", "reward_delta")
    )


def _source_files(source: Path) -> tuple[Path, ...]:
    if source.is_file():
        if source.suffix != ".jsonl":
            raise PreferenceArmsError(f"source file must be JSONL: {source}")
        return (source,)
    if source.is_dir():
        files = tuple(sorted(source.rglob("*.jsonl")))
        if not files:
            raise PreferenceArmsError(f"no JSONL files under source: {source}")
        return files
    raise PreferenceArmsError(f"source does not exist: {source}")


def scan_source(
    source: Path,
    *,
    min_distance: float = DEFAULT_MIN_ARM_DISTANCE,
    require_isolation: bool = True,
    trusted_isolation: str | None = None,
    require_trusted_isolation: bool = False,
) -> ArmScan:
    """Gate every preference pair under ``source``."""

    source = Path(source)
    min_distance = _validated_distance_floor(min_distance)
    decisions: list[ArmDecision] = []
    reasons: Counter[str] = Counter()
    skipped = 0

    for path in _source_files(source):
        relative = path.relative_to(source).as_posix() if source.is_dir() else path.name
        for line_number, raw_line in enumerate(path.read_bytes().splitlines(), 1):
            if not raw_line.strip():
                continue
            try:
                record = json.loads(raw_line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise PreferenceArmsError(
                    f"{relative}:{line_number}: unreadable JSON: {exc}"
                ) from exc
            if not _is_preference_candidate(record):
                skipped += 1
                continue
            decision = check_pair(
                record,
                source_path=relative,
                source_line=line_number,
                min_distance=min_distance,
                require_isolation=require_isolation,
                trusted_isolation=trusted_isolation,
                require_trusted_isolation=require_trusted_isolation,
            )
            reasons.update(decision.reason_codes)
            decisions.append(decision)

    distances = [d.arm_distance for d in decisions if d.arm_distance is not None]
    blocked = [d for d in decisions if d.blocked]
    pairs = len(decisions)
    summary = {
        "gate": {"name": GATE_NAME, "version": GATE_VERSION},
        "source": str(source),
        "min_arm_distance": min_distance,
        "require_isolation": require_isolation,
        "require_trusted_isolation": require_trusted_isolation,
        "trusted_isolation": trusted_isolation,
        "preference_pairs": pairs,
        "skipped_non_preference_records": skipped,
        "blocked_pairs": len(blocked),
        "independent_pairs": pairs - len(blocked),
        "same_context_pairs": sum(1 for d in decisions if d.same_context),
        "two_session_pairs": sum(1 for d in decisions if d.isolation == TWO_SESSION),
        "trusted_two_session_pairs": sum(
            1 for d in decisions if d.trusted_isolation == TWO_SESSION
        ),
        "context_purity_pct": (
            round(100 * sum(1 for d in decisions if d.same_context) / pairs, 1) if pairs else 0.0
        ),
        "observed_min_arm_distance": min(distances) if distances else None,
        "observed_max_arm_distance": max(distances) if distances else None,
        "reason_codes": dict(sorted(reasons.items())),
    }
    return ArmScan(tuple(decisions), summary)






def _min_distance(raw: str) -> float:
    try:
        value = float(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"not a number: {raw}") from exc
    try:
        return _validated_distance_floor(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"--min-distance must be a finite value in [0, 1): {raw}"
        ) from exc
























def verify_diagnosis_handoff(
    staging_dir: Path,
    diagnosis_files: Sequence[str],
    *,
    _stage_fd: int | None = None,
) -> dict[str, Any]:
    """Verify one bounded diagnosis-only bridge without reading arm payloads.

    The returned receipt contains names, byte counts, and SHA-256 digests only.
    It deliberately never returns diagnosis content or inspects rejected-arm
    scratch files, so the verifier remains arm-payload-blind even while it
    validates the bounded diagnosis envelope.
    """

    stage = Path(staging_dir)
    if not stage.is_absolute():
        raise PreferenceArmsError("staging directory must be an absolute path")
    try:
        stage_stat = stage.lstat()
    except OSError as exc:
        raise PreferenceArmsError(f"staging directory cannot be inspected: {stage}: {exc}") from exc
    if stat.S_ISLNK(stage_stat.st_mode) or not stat.S_ISDIR(stage_stat.st_mode):
        raise PreferenceArmsError(f"staging directory is not a real directory: {stage}")
    try:
        resolved_stage = stage.resolve(strict=True)
    except OSError as exc:
        raise PreferenceArmsError(f"staging directory cannot be resolved: {stage}: {exc}") from exc
    if resolved_stage != stage:
        raise PreferenceArmsError(
            f"staging directory contains a symlink or non-canonical path: {stage}"
        )

    stage_match = _STAGING_NAME_RE.fullmatch(stage.name)
    if stage_match is None:
        raise PreferenceArmsError(
            "staging directory must end in r<positive round>-<32 lowercase hex token>"
        )
    factory = stage.parent.name
    if _FACTORY_SLUG_RE.fullmatch(factory) is None:
        raise PreferenceArmsError(f"invalid factory slug in staging path: {factory!r}")
    round_number = int(stage_match.group("round"))
    round_text = f"{round_number:02d}"

    if isinstance(diagnosis_files, (str, bytes)):
        raise PreferenceArmsError("diagnosis files must be a sequence of basenames")
    names = tuple(diagnosis_files)
    if not names:
        raise PreferenceArmsError("at least one diagnosis file is required")
    if len(set(names)) != len(names):
        raise PreferenceArmsError("diagnosis filenames must be unique")

    for name in names:
        if not isinstance(name, str) or Path(name).name != name:
            raise PreferenceArmsError(f"diagnosis filename must be a basename: {name!r}")
        name_match = _DIAGNOSIS_NAME_RE.fullmatch(name)
        if name_match is None or name_match.group("round") != round_text:
            raise PreferenceArmsError(
                f"diagnosis filename does not match staging round r{round_text}: {name!r}"
            )

    expected_names = diagnosis_filenames(round_number, len(names))
    if names != expected_names:
        raise PreferenceArmsError(
            "diagnosis filenames must be the contiguous ordered allowlist "
            + ", ".join(expected_names)
        )

    stage_fd = _stage_fd if _stage_fd is not None else -1
    owns_stage_fd = _stage_fd is None
    try:
        if owns_stage_fd:
            stage_fd = _open_canonical_directory(stage, label="staging directory")
        _require_open_directory_identity(stage, stage_fd, label="staging directory")
        verified: list[dict[str, Any]] = []
        for name in names:
            payload = _read_regular_artifact_from_directory(
                stage_fd,
                name,
                label="diagnosis file",
                max_bytes=MAX_DIAGNOSIS_BYTES,
            )
            validate_diagnosis_document(payload, label=f"diagnosis file {name}")
            verified.append(
                {
                    "name": name,
                    "bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            )
        _require_open_directory_identity(stage, stage_fd, label="staging directory")
    finally:
        if owns_stage_fd and stage_fd >= 0:
            os.close(stage_fd)

    return {
        "version": HANDOFF_RECEIPT_VERSION,
        "factory": factory,
        "round": round_number,
        "staging_dir": str(stage),
        "reservation_token": stage_match.group("token"),
        "diagnosis_files": verified,
    }


def write_diagnosis_handoff_receipt(
    staging_dir: Path,
    diagnosis_files: Sequence[str],
) -> dict[str, Any]:
    """Verify the handoff and exclusively persist its canonical receipt."""

    stage = Path(staging_dir)
    stage_fd = -1
    receipt_fd = -1
    created = False
    receipt: dict[str, Any] | None = None
    receipt_name = "diagnosis-handoff-receipt.json"
    receipt_path = stage / receipt_name
    try:
        stage_fd = _open_canonical_directory(stage, label="staging directory")
        receipt = verify_diagnosis_handoff(stage, diagnosis_files, _stage_fd=stage_fd)
        round_text = f"{receipt['round']:02d}"
        receipt_name = diagnosis_receipt_filename(receipt["round"])
        receipt_path = stage / receipt_name
        encoded = (
            json.dumps(receipt, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        _require_open_directory_identity(stage, stage_fd, label="staging directory")
        session_b_outputs = _session_b_outputs(os.listdir(stage_fd), round_text)
        if session_b_outputs:
            raise PreferenceArmsError(
                "diagnosis receipt must be created before Session B outputs: "
                + ", ".join(session_b_outputs)
            )
        receipt_fd = os.open(receipt_name, flags, 0o600, dir_fd=stage_fd)
        created = True
        with os.fdopen(receipt_fd, "wb") as handle:
            receipt_fd = -1
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
            os.fchmod(handle.fileno(), 0o400)
        # This directory fsync is the receipt-before-Session-B ordering point.
        # An output created after it is later than the durable receipt even if
        # the verifier process has not returned its bounded JSON summary yet.
        os.fsync(stage_fd)
        post_create_outputs = _session_b_outputs(os.listdir(stage_fd), round_text)
        _require_open_directory_identity(stage, stage_fd, label="staging directory")
        final_outputs = _session_b_outputs(os.listdir(stage_fd), round_text)
        if post_create_outputs:
            raise PreferenceArmsError(
                "Session B outputs appeared during diagnosis receipt creation: "
                + ", ".join(post_create_outputs)
            )
        if final_outputs:
            raise PreferenceArmsError(
                "Session B outputs appeared during diagnosis receipt finalization: "
                + ", ".join(final_outputs)
            )
    except (OSError, PreferenceArmsError) as exc:
        if receipt_fd >= 0:
            os.close(receipt_fd)
            receipt_fd = -1
        if created and stage_fd >= 0:
            try:
                os.unlink(receipt_name, dir_fd=stage_fd)
                os.fsync(stage_fd)
            except FileNotFoundError:
                pass
        if isinstance(exc, PreferenceArmsError):
            raise
        raise PreferenceArmsError(
            f"diagnosis handoff receipt cannot be created exclusively: {receipt_path}: {exc}"
        ) from exc
    finally:
        if receipt_fd >= 0:
            os.close(receipt_fd)
        if stage_fd >= 0:
            os.close(stage_fd)
    if receipt is None:  # pragma: no cover - every successful path assigns it
        raise AssertionError("diagnosis receipt was not constructed")
    return receipt






def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="gate preference arms without writing anything")
    scan.add_argument("source", type=Path)
    scan.add_argument("--json", action="store_true", help="emit the full report")
    scan.add_argument(
        "--min-distance",
        type=_min_distance,
        default=DEFAULT_MIN_ARM_DISTANCE,
        help=(
            "lexical arm-distance floor; a pair must exceed it "
            f"(fixture-calibrated default: {DEFAULT_MIN_ARM_DISTANCE})"
        ),
    )
    scan.add_argument(
        "--no-require-isolation",
        dest="require_isolation",
        action="store_false",
        help=(
            "report but do not block on a missing meta.isolation attestation "
            "(legacy corpora predating the two-session protocol)"
        ),
    )
    verify_handoff = subparsers.add_parser(
        "verify-handoff",
        help="verify diagnosis basenames, regular files, bytes, and SHA-256 digests",
    )
    verify_handoff.add_argument("staging_dir", type=Path)
    verify_handoff.add_argument(
        "--file",
        dest="diagnosis_files",
        action="append",
        required=True,
        help="expected diagnosis basename; repeat in contiguous numeric order",
    )
    verify_handoff.add_argument(
        "--write-receipt",
        action="store_true",
        help="exclusively write the canonical round-scoped receipt before Session B",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "verify-handoff":
        try:
            verifier = (
                write_diagnosis_handoff_receipt if args.write_receipt else verify_diagnosis_handoff
            )
            receipt = verifier(args.staging_dir, args.diagnosis_files)
        except (OSError, PreferenceArmsError, ValueError) as exc:
            print(f"diagnosis handoff verification failed: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(receipt, sort_keys=True, ensure_ascii=False))
        return 0

    try:
        scan = scan_source(
            args.source,
            min_distance=args.min_distance,
            require_isolation=args.require_isolation,
        )
    except (OSError, PreferenceArmsError, ValueError) as exc:
        print(f"preference arm gate failed: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(
            json.dumps(
                {
                    "summary": scan.summary,
                    "decisions": [d.as_dict() for d in scan.decisions],
                },
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
        )
    else:
        print(render_human(scan))

    # Verdict lines go to stderr so stdout stays a parseable report in both
    # human and --json modes.
    if scan.blocked:
        print(
            f"arm gate: FAIL — {scan.summary['blocked_pairs']} pair(s) blocked",
            file=sys.stderr,
        )
        return 1
    if not scan.summary["preference_pairs"]:
        # Fail closed: an empty scan means the path or glob is wrong, not that
        # the round is clean.
        print("arm gate: FAIL — no preference pairs found", file=sys.stderr)
        return 1
    print(
        "arm gate: PASS (independent arms, same context, two-session attested)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
