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
2. **Independent arms** — the *contrastive* surfaces of the two arms (every
   field except the shared context and bookkeeping ``meta``) must sit more
   than ``--min-distance`` apart. Distance is ``1 - cosine_similarity`` over
   path-scoped lexical term-frequency vectors. This metric has its own
   fixture-calibrated floor; it is not presented as equivalent to an
   embedding model. A separate structural check rejects copies that differ
   only in a gate label, independent of vector length.

The read-only gate requires each pair to declare
``meta.isolation == "two-session"``. Publication additionally requires a
publisher-controlled isolation value recorded in the exclusive reservation
marker; record metadata alone is never treated as proof of the protocol.

Read-only scan (exit 1 when any pair is blocked)::

    python3 pipelines/preference_arms.py scan <batch-or-dir> [--json]

``source`` may be one JSONL file or a directory scanned recursively for
``*.jsonl``. Records without preference-pair fields are counted and skipped.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from curate_preferences import canonical_json, context_is_pure  # noqa: E402
GATE_NAME = "independent-preference-arms"
GATE_VERSION = "1.1.0"

#: Minimum lexical ``1 - cosine_similarity`` between the two arms'
#: contrastive surfaces. This is calibrated against the committed passing,
#: verbatim, light-edit, and multilingual fixtures. It intentionally does not
#: reuse the unrelated embedding threshold from ``quality_gate``.
DEFAULT_MIN_ARM_DISTANCE: float = 0.03

#: The only accepted ``meta.isolation`` value. Anything else is the
#: deprecated single-context generation path.
TWO_SESSION = "two-session"

#: Fields excluded from the contrastive surface. ``state`` and
#: ``proposed_action`` are identical by the purity gate and would swamp the
#: metric; ``id`` and ``meta`` are bookkeeping whose per-side identifiers and
#: ``chosen``/``rejected`` tags would manufacture distance no learner sees.
CONTEXT_FIELDS = ("state", "proposed_action")
EXCLUDED_FROM_CONTRAST = frozenset(CONTEXT_FIELDS + ("id", "meta"))

REASON_MALFORMED = "PREFERENCE_PAIR_MALFORMED"
REASON_CONTEXT_DIVERGES = "PREFERENCE_CONTEXT_DIVERGES"
REASON_NEAR_VERBATIM = "PREFERENCE_ARMS_NEAR_VERBATIM"
REASON_CONTRAST_EMPTY = "PREFERENCE_ARM_CONTRAST_EMPTY"
REASON_ISOLATION_UNDECLARED = "PREFERENCE_ARMS_ISOLATION_UNDECLARED"
REASON_ISOLATION_CONFLICT = "PREFERENCE_ARMS_ISOLATION_CONFLICT"
REASON_SINGLE_SESSION = "PREFERENCE_ARMS_SINGLE_SESSION_PATH"
REASON_ISOLATION_UNTRUSTED = "PREFERENCE_ARMS_ISOLATION_UNTRUSTED"
REASON_LABEL_ONLY_COPY = "PREFERENCE_ARMS_LABEL_ONLY_COPY"

_GATE_LABEL_PATHS = frozenset({("safety_decision", "decision")})


class PreferenceArmsError(RuntimeError):
    """Raised when a source cannot be read as preference JSONL."""


@dataclass(frozen=True)
class ArmDecision:
    """One deterministic pair-level decision. ``blocked`` gates the round."""

    source_path: str
    source_line: int
    record_id: str | None
    same_context: bool
    isolation: str | None
    trusted_isolation: str | None
    arm_distance: float | None
    cosine_similarity: float | None
    reason_codes: tuple[str, ...] = ()

    @property
    def blocked(self) -> bool:
        return bool(self.reason_codes)

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "source_line": self.source_line,
            "record_id": self.record_id,
            "same_context": self.same_context,
            "isolation": self.isolation,
            "trusted_isolation": self.trusted_isolation,
            "arm_distance": self.arm_distance,
            "cosine_similarity": self.cosine_similarity,
            "reason_codes": list(self.reason_codes),
            "blocked": self.blocked,
        }


@dataclass(frozen=True)
class ArmScan:
    """Per-pair decisions plus aggregate counts for one source."""

    decisions: tuple[ArmDecision, ...] = ()
    summary: dict[str, Any] = field(default_factory=dict)

    @property
    def blocked(self) -> bool:
        return bool(self.summary.get("blocked_pairs"))


def _contrast_surface(arm: dict[str, Any]) -> dict[str, Any]:
    """Return the arm fields that carry the preference signal."""

    return {
        key: value for key, value in arm.items() if key not in EXCLUDED_FROM_CONTRAST
    }


def _unicode_terms(value: str) -> tuple[str, ...]:
    """Tokenize words without turning unspaced Unicode into one atom.

    Compatibility decomposition keeps accented and unaccented spellings on
    the same lexical stem; combining marks do not manufacture independence.
    ASCII words stay intact. Other letters and digits are emitted as
    normalized code-point terms, so a one-character edit in unspaced CJK
    changes one term instead of replacing the entire rationale.
    """

    normalized = unicodedata.normalize("NFKD", value.casefold())
    terms: list[str] = []
    ascii_word: list[str] = []

    def flush_ascii() -> None:
        if ascii_word:
            terms.append("".join(ascii_word))
            ascii_word.clear()

    for character in normalized:
        if unicodedata.combining(character):
            continue
        if character.isascii() and character.isalnum():
            ascii_word.append(character)
        elif character.isalnum():
            flush_ascii()
            terms.append(character)
        else:
            flush_ascii()
    flush_ascii()
    return tuple(terms)


def _without_gate_labels(value: Any, path: tuple[str, ...] = ()) -> Any:
    """Return a comparison value with only recognized gate labels removed."""

    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            child_path = (*path, str(key))
            if child_path in _GATE_LABEL_PATHS:
                continue
            result[key] = _without_gate_labels(item, child_path)
        return result
    if isinstance(value, list):
        return [_without_gate_labels(item, path) for item in value]
    return value


def differs_only_by_gate_label(
    chosen: dict[str, Any], rejected: dict[str, Any]
) -> bool:
    """Whether the sole contrastive change is a safety gate decision label."""

    chosen_surface = _contrast_surface(chosen)
    rejected_surface = _contrast_surface(rejected)
    if canonical_json(chosen_surface) == canonical_json(rejected_surface):
        return False
    return canonical_json(_without_gate_labels(chosen_surface)) == canonical_json(
        _without_gate_labels(rejected_surface)
    )


def _collect_terms(value: Any, path: str, terms: Counter[str]) -> None:
    if isinstance(value, dict):
        for key in sorted(value):
            _collect_terms(value[key], f"{path}.{key}", terms)
        return
    if isinstance(value, list):
        # Position-insensitive: a reordered list is not a different arm.
        for item in value:
            _collect_terms(item, f"{path}[]", terms)
        return
    if isinstance(value, str):
        words = _unicode_terms(value)
        if words:
            for word in words:
                terms[f"{path}:{word}"] += 1
            return
    # Non-strings (and strings with no word characters) stay atomic so that
    # 0.2 and -0.2, or true and false, are never the same term.
    terms[f"{path}={canonical_json(value)}"] += 1


def arm_terms(arm: dict[str, Any]) -> Counter[str]:
    """Return path-scoped term frequencies for one arm's contrast surface."""

    terms: Counter[str] = Counter()
    _collect_terms(_contrast_surface(arm), "", terms)
    return terms


def cosine_similarity(left: Counter[str], right: Counter[str]) -> float:
    """Cosine similarity of two term-frequency vectors, clamped to [0, 1]."""

    left_norm = math.sqrt(sum(count * count for count in left.values()))
    right_norm = math.sqrt(sum(count * count for count in right.values()))
    if not left_norm or not right_norm:
        # An empty surface is degenerate, not distant. Callers flag it.
        return 1.0 if left_norm == right_norm else 0.0
    smaller, larger = (left, right) if len(left) <= len(right) else (right, left)
    dot = sum(count * larger[term] for term, count in smaller.items())
    # Clamp and round: identical vectors must land on exactly 1.0 rather than
    # 1 - 2e-16, and no decision here turns on the twelfth decimal.
    return round(max(0.0, min(1.0, dot / (left_norm * right_norm))), 12)


def arm_distance(chosen: dict[str, Any], rejected: dict[str, Any]) -> float:
    """Return ``1 - cosine_similarity`` between the two contrast surfaces."""

    return 1.0 - cosine_similarity(arm_terms(chosen), arm_terms(rejected))


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

    chosen_terms = arm_terms(chosen)
    rejected_terms = arm_terms(rejected)
    if not chosen_terms or not rejected_terms:
        reasons.append(REASON_CONTRAST_EMPTY)
    if differs_only_by_gate_label(chosen, rejected):
        reasons.append(REASON_LABEL_ONLY_COPY)
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
        relative = (
            path.relative_to(source).as_posix() if source.is_dir() else path.name
        )
        for line_number, raw_line in enumerate(
            path.read_bytes().splitlines(), 1
        ):
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
            round(100 * sum(1 for d in decisions if d.same_context) / pairs, 1)
            if pairs
            else 0.0
        ),
        "observed_min_arm_distance": min(distances) if distances else None,
        "observed_max_arm_distance": max(distances) if distances else None,
        "reason_codes": dict(sorted(reasons.items())),
    }
    return ArmScan(tuple(decisions), summary)


def render_human(scan: ArmScan) -> str:
    summary = scan.summary
    lines = [
        f"Preference pairs: {summary['preference_pairs']}",
        f"Same-context: {summary['same_context_pairs']}"
        f" ({summary['context_purity_pct']}%)",
        f"Two-session attested: {summary['two_session_pairs']}",
        f"Publisher-trusted two-session: {summary['trusted_two_session_pairs']}",
        f"Min arm distance required: > {summary['min_arm_distance']}",
        f"Observed arm distance: {summary['observed_min_arm_distance']}"
        f" .. {summary['observed_max_arm_distance']}",
        f"Blocked: {summary['blocked_pairs']}",
    ]
    for decision in scan.decisions:
        location = f"{decision.source_path}:{decision.source_line}"
        record_id = decision.record_id or "<no-id>"
        verdict = (
            "BLOCKED [" + ",".join(decision.reason_codes) + "]"
            if decision.blocked
            else "ok"
        )
        lines.append(
            f"- {location} {record_id}: distance={decision.arm_distance} {verdict}"
        )
    return "\n".join(lines)


def _validated_distance_floor(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"arm-distance floor must be numeric: {value!r}")
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value < 1.0:
        raise ValueError(
            f"arm-distance floor must be a finite value in [0, 1): {value!r}"
        )
    return value


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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser(
        "scan", help="gate preference arms without writing anything"
    )
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
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
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
