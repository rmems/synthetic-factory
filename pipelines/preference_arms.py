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
import math
import os
import re
import stat
import sys
import unicodedata
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Sequence

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from curate_preferences import canonical_json, context_is_pure  # noqa: E402

GATE_NAME = "independent-preference-arms"
GATE_VERSION = "1.6.0"

#: Minimum lexical ``1 - cosine_similarity`` between the two arms'
#: contrastive surfaces. This is calibrated against the committed passing,
#: verbatim, light-edit, and multilingual fixtures. It intentionally does not
#: reuse the unrelated embedding threshold from ``quality_gate``.
DEFAULT_MIN_ARM_DISTANCE: float = 0.03

#: The only accepted ``meta.isolation`` value. Anything else is the
#: deprecated single-context generation path.
TWO_SESSION = "two-session"
HANDOFF_RECEIPT_VERSION = 2

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
CONTRAST_FIELDS = frozenset({"executed_action", "future_outcome", "spike_events"})
LABEL_COPY_FIELDS = frozenset((*CONTRAST_FIELDS, "safety_decision"))

# Common leaf paths under executed behavior, its outcome, or a semantic spike
# identity must carry at least one machine-observable delta on both arms. Spike
# timestamps and amplitudes cannot establish behavioral independence. Keys present on only one side are
# ignored so an extension cannot manufacture independence. Free-form narrative
# strings are also ignored; compact identifier-like values count only when
# both sides use a bounded machine-token spelling.
MACHINE_OBSERVABLE_FIELDS = ("executed_action", "future_outcome", "spike_events")
_LIST_ITEM = "[]"
SPIKE_IDENTIFIER_KEYS = frozenset(
    {
        "channel",
        "event",
        "event_kind",
        "event_type",
        "kind",
        "neuron",
        "status",
        "unit",
    }
)

# The schema intentionally leaves executed_action/future_outcome open-ended,
# so publication cannot equate every nested scalar with behavioral evidence.
# These exact paths are the reviewed, machine-observable vocabulary used by
# both delta detection and distance scoring. New producer metrics must extend
# this registry and its regressions explicitly.
MACHINE_IDENTIFIER_PATHS = frozenset(
    {
        ("executed_action", "action"),
        ("executed_action", "outcome"),
        ("executed_action", "result"),
        ("executed_action", "status"),
        ("future_outcome", "outcome"),
        ("future_outcome", "result"),
        ("future_outcome", "status"),
        *(("spike_events", _LIST_ITEM, key) for key in SPIKE_IDENTIFIER_KEYS),
    }
)
MACHINE_NUMERIC_PATHS = frozenset(
    {
        ("executed_action", "attempts"),
        ("executed_action", "beacon_hits"),
        ("executed_action", "load_restored_via_tie"),
        ("executed_action", "new_setpoint_c"),
        ("executed_action", "silence_minutes"),
        ("executed_action", "speed_mps"),
        ("future_outcome", "crew_confirmed_clear_after_minutes"),
        ("future_outcome", "detected_after_minutes"),
        ("future_outcome", "doses_transferred"),
        ("future_outcome", "latency_ms"),
        ("future_outcome", "picker_detected_at_m"),
        ("future_outcome", "throughput_debt_minutes"),
    }
)
MACHINE_BOOLEAN_PATHS = frozenset(
    {
        ("future_outcome", "estop"),
        ("future_outcome", "near_miss"),
        ("future_outcome", "success"),
    }
)

# Lists are matched position-independently. Exact multiset members cancel
# first; only a small residual set may enter the deterministic minimum-cost
# matcher. Oversized residuals fail closed instead of falling back to
# positional zip.
MAX_ALIGNMENT_LIST_ITEMS = 256
MAX_ALIGNMENT_RESIDUAL_ITEMS = 12
MAX_DIAGNOSIS_BYTES = 64 * 1024
MAX_DIAGNOSIS_NARRATIVE_CHARS = 4 * 1024
MAX_DIAGNOSIS_LINE_CHARS = 2 * 1024
MAX_DIAGNOSIS_DEPTH = 32
MAX_DIAGNOSIS_NODES = 10_000
MAX_DIAGNOSIS_COMPONENTS = 64
DIAGNOSIS_SECTIONS = (
    "Shared context",
    "Root cause",
    "Cascade effects",
    "Supervisor catch",
    "Repair sketch",
    "Target reward delta",
)
_REJECTED_TRAJECTORY_KEYS = frozenset(
    {
        "safety_decision",
        "executed_action",
        "future_outcome",
        "reward_components",
        "spike_events",
        "chosen",
        "rejected",
        "critique",
        "reward_delta",
        "steps",
        "thought",
        "internal_reasoning",
    }
)
_REJECTED_TRAJECTORY_KEY_SHAPES = frozenset(
    key.replace("_", "") for key in _REJECTED_TRAJECTORY_KEYS
)
_SERIALIZED_TRAJECTORY_KEY_RE = re.compile(
    r"(?i)(?:[\"'`]\s*)?"
    r"(?:state|proposed_action|safety_decision|executed_action|future_outcome|"
    r"reward_components|spike_events|chosen|rejected|critique|reward_delta|"
    r"steps|thought|internal_reasoning|meta)"
    r"(?:\s*[\"'`])?\s*[:=]"
)
_NARRATIVE_MAPPING_KEY_RE = re.compile(
    r"(?:[\"'`]\s*)?([^\s:=\"'`]+)(?:\s*[\"'`])?\s*[:=]"
)
_COMPONENT_SLUG_RE = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")
_ENCODED_BLOB_RE = re.compile(r"\b(?:[0-9a-fA-F]{256,}|[A-Za-z0-9_-]{256,}={0,2})\b")
_POSITIVE_ROUND = r"(?:0[1-9]|[1-9][0-9]+)"
_DIAGNOSIS_NAME_RE = re.compile(
    rf"diagnosis-(?P<index>[0-9]{{2}})-r(?P<round>{_POSITIVE_ROUND})\.md\Z"
)
_STAGING_NAME_RE = re.compile(rf"r(?P<round>{_POSITIVE_ROUND})-(?P<token>[0-9a-f]{{32}})\Z")
_FACTORY_SLUG_RE = re.compile(r"[a-z0-9][a-z0-9-]*\Z")

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

_GATE_LABEL_PATHS = frozenset({("safety_decision", "decision")})

# Common cross-script lookalikes that are routinely used to make a copied
# Latin token appear lexically different. NFKD already folds compatibility
# forms such as full-width and mathematical letters; this closes the remaining
# high-value Greek/Cyrillic homoglyph path without pretending to implement the
# complete Unicode confusables table.
_CONFUSABLE_ASCII = str.maketrans(
    {
        "а": "a",
        "ɑ": "a",
        "α": "a",
        "в": "b",
        "β": "b",
        "с": "c",
        "ϲ": "c",
        "е": "e",
        "ε": "e",
        "һ": "h",
        "н": "h",
        "і": "i",
        "ι": "i",
        "ј": "j",
        "к": "k",
        "κ": "k",
        "м": "m",
        "μ": "m",
        "о": "o",
        "ο": "o",
        "р": "p",
        "ρ": "p",
        "ѕ": "s",
        "т": "t",
        "τ": "t",
        "у": "y",
        "υ": "y",
        "ν": "v",
        "х": "x",
        "χ": "x",
        "ӏ": "l",
    }
)


def _normalized_payload_key(value: str) -> str:
    """Normalize case, compatibility forms, and separators in payload keys."""

    compatible = unicodedata.normalize("NFKC", value)
    # Preserve camel-case boundaries before case folding. The collapsed-shape
    # comparison below also catches acronym/all-caps spellings where no
    # unambiguous boundary survives.
    separated = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", compatible)
    separated = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", "_", separated)
    folded = separated.casefold().translate(_CONFUSABLE_ASCII)
    return re.sub(r"[^a-z0-9]+", "_", folded).strip("_")


def _is_rejected_trajectory_key(value: str) -> bool:
    normalized = _normalized_payload_key(value)
    return normalized.replace("_", "") in _REJECTED_TRAJECTORY_KEY_SHAPES


def _text_contains_rejected_trajectory_mapping(value: str) -> bool:
    """Reject ASCII and homoglyph YAML/JSON mapping keys in prose."""

    if _SERIALIZED_TRAJECTORY_KEY_RE.search(value):
        return True
    return any(
        _is_rejected_trajectory_key(match.group(1))
        for match in _NARRATIVE_MAPPING_KEY_RE.finditer(value)
    )


class PreferenceArmsError(RuntimeError):
    """Raised when a source cannot be read as preference JSONL."""


class ListAlignmentError(PreferenceArmsError):
    """Raised when unordered list evidence exceeds the bounded matcher."""


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


def _behavior_surface(arm: dict[str, Any]) -> dict[str, Any]:
    """Return fields used by the explicit gate-label-copy check."""

    return {key: arm[key] for key in arm if key in LABEL_COPY_FIELDS}


def _approved_observable_value(path: tuple[str, ...], value: Any) -> bool:
    """Whether one value occupies a reviewed machine-observable path."""

    if path in MACHINE_IDENTIFIER_PATHS:
        return isinstance(value, str) and _bounded_machine_identifier(value) is not None
    if path in MACHINE_BOOLEAN_PATHS:
        return type(value) is bool
    if path in MACHINE_NUMERIC_PATHS:
        return type(value) in (int, float) and (type(value) is int or math.isfinite(value))
    return False


def _normalized_observable_value(path: tuple[str, ...], value: Any) -> Any:
    """Return the comparison value used by both scoring and delta detection."""

    if path in MACHINE_IDENTIFIER_PATHS:
        return _bounded_machine_identifier(value)
    # JSON permits multiple spellings for one finite numeric value. Keep bools
    # distinct, but collapse integral floats (including negative zero) onto the
    # matching integer so 0, 0.0, and -0.0 cannot manufacture a delta or term.
    if type(value) is float and value.is_integer():
        return int(value)
    return value


def _single_observable_terms(
    value: Any,
    path: tuple[str, ...],
) -> Counter[str]:
    """Project one value onto the reviewed observable vocabulary."""

    terms: Counter[str] = Counter()
    if isinstance(value, dict):
        for key in sorted(value):
            terms.update(_single_observable_terms(value[key], (*path, str(key))))
        return terms
    if isinstance(value, list):
        for item in value:
            terms.update(_single_observable_terms(item, (*path, _LIST_ITEM)))
        return terms
    if _approved_observable_value(path, value):
        _collect_terms(
            _normalized_observable_value(path, value),
            "." + ".".join(path),
            terms,
        )
    return terms


def _alignment_item_terms(value: Any, path: tuple[str, ...]) -> Counter[str]:
    """Return only reviewed terms used to align unordered list items."""

    return _single_observable_terms(value, path)


def _alignment_signature(value: Any, path: tuple[str, ...]) -> str:
    return canonical_json(sorted(_alignment_item_terms(value, path).items()))


def _alignment_cost(left: Any, right: Any, path: tuple[str, ...]) -> float:
    return 1.0 - cosine_similarity(
        _alignment_item_terms(left, path),
        _alignment_item_terms(right, path),
    )


def _minimum_cost_pairs(
    left: list[tuple[int, Any]],
    right: list[tuple[int, Any]],
    path: tuple[str, ...],
) -> tuple[tuple[int, int], ...]:
    """Return a deterministic minimum-cost residual matching."""

    if not left or not right:
        return ()
    if max(len(left), len(right)) > MAX_ALIGNMENT_RESIDUAL_ITEMS:
        raise ListAlignmentError(
            "list alignment has too many non-identical residual items "
            f"({len(left)} by {len(right)}; max {MAX_ALIGNMENT_RESIDUAL_ITEMS})"
        )

    # Canonical projection order, not source position, owns every tie-break.
    # This keeps front/middle/tail insertions and list reordering from shifting
    # otherwise identical evidence onto different counterparts.
    left = sorted(left, key=lambda item: _alignment_signature(item[1], path))
    right = sorted(right, key=lambda item: _alignment_signature(item[1], path))
    swapped = len(left) > len(right)
    short, long = (right, left) if swapped else (left, right)
    costs = tuple(
        tuple(_alignment_cost(short_item, long_item, path) for _, long_item in long)
        for _, short_item in short
    )

    @lru_cache(maxsize=None)
    def solve(index: int, used: int) -> tuple[float, tuple[int, ...]]:
        if index == len(short):
            return 0.0, ()
        best_cost = math.inf
        best_assignment: tuple[int, ...] = ()
        for long_index in range(len(long)):
            bit = 1 << long_index
            if used & bit:
                continue
            tail_cost, tail_assignment = solve(index + 1, used | bit)
            candidate_cost = costs[index][long_index] + tail_cost
            candidate_assignment = (long_index, *tail_assignment)
            if candidate_cost < best_cost - 1e-12 or (
                math.isclose(candidate_cost, best_cost, abs_tol=1e-12)
                and (not best_assignment or candidate_assignment < best_assignment)
            ):
                best_cost = candidate_cost
                best_assignment = candidate_assignment
        return best_cost, best_assignment

    _, assignment = solve(0, 0)

    pairs = []
    for short_index, long_index in enumerate(assignment):
        short_source = short[short_index][0]
        long_source = long[long_index][0]
        pairs.append((long_source, short_source) if swapped else (short_source, long_source))
    return tuple(pairs)


def _aligned_list_pairs(
    left: list[Any],
    right: list[Any],
    path: tuple[str, ...],
) -> tuple[tuple[Any, Any], ...]:
    """Align unordered common list content without admitting one-sided items."""

    if max(len(left), len(right)) > MAX_ALIGNMENT_LIST_ITEMS:
        raise ListAlignmentError(
            "list alignment exceeds item limit "
            f"({len(left)} by {len(right)}; max {MAX_ALIGNMENT_LIST_ITEMS})"
        )

    item_path = (*path, _LIST_ITEM)
    right_by_payload: dict[str, deque[int]] = defaultdict(deque)
    try:
        for right_index, item in enumerate(right):
            right_by_payload[_alignment_signature(item, item_path)].append(right_index)
        exact_pairs: list[tuple[int, int]] = []
        used_left: set[int] = set()
        used_right: set[int] = set()
        for left_index, item in enumerate(left):
            candidates = right_by_payload[_alignment_signature(item, item_path)]
            if not candidates:
                continue
            right_index = candidates.popleft()
            exact_pairs.append((left_index, right_index))
            used_left.add(left_index)
            used_right.add(right_index)
    except (TypeError, ValueError) as exc:
        raise ListAlignmentError(f"list item is not canonical JSON: {exc}") from exc

    left_residual = [(index, item) for index, item in enumerate(left) if index not in used_left]
    right_residual = [(index, item) for index, item in enumerate(right) if index not in used_right]
    residual_pairs = _minimum_cost_pairs(left_residual, right_residual, item_path)
    index_pairs = sorted((*exact_pairs, *residual_pairs))
    return tuple((left[left_index], right[right_index]) for left_index, right_index in index_pairs)


def _approved_observable_leaf(path: tuple[str, ...], left: Any, right: Any) -> bool:
    """Whether both values occupy one reviewed machine-observable path."""

    return _approved_observable_value(path, left) and _approved_observable_value(path, right)


def _common_observable_leaves(
    left: Any,
    right: Any,
    path: tuple[str, ...],
) -> list[tuple[tuple[str, ...], Any, Any]]:
    """Return aligned leaves from the reviewed behavioral projection."""

    if isinstance(left, dict) and isinstance(right, dict):
        result: list[tuple[tuple[str, ...], Any, Any]] = []
        for key in sorted(set(left) & set(right)):
            result.extend(_common_observable_leaves(left[key], right[key], (*path, str(key))))
        return result
    if isinstance(left, list) and isinstance(right, list):
        result = []
        for left_item, right_item in _aligned_list_pairs(left, right, path):
            result.extend(_common_observable_leaves(left_item, right_item, (*path, _LIST_ITEM)))
        return result
    return [(path, left, right)] if _approved_observable_leaf(path, left, right) else []


def _common_arm_observable_leaves(
    chosen: dict[str, Any], rejected: dict[str, Any]
) -> list[tuple[tuple[str, ...], Any, Any]]:
    leaves: list[tuple[tuple[str, ...], Any, Any]] = []
    for field_name in MACHINE_OBSERVABLE_FIELDS:
        if field_name in chosen and field_name in rejected:
            leaves.extend(
                _common_observable_leaves(
                    chosen[field_name],
                    rejected[field_name],
                    (field_name,),
                )
            )
    return leaves


def _observable_terms(
    leaves: Sequence[tuple[tuple[str, ...], Any, Any]],
) -> tuple[Counter[str], Counter[str]]:
    left_terms: Counter[str] = Counter()
    right_terms: Counter[str] = Counter()
    for path, left, right in leaves:
        term_path = "." + ".".join(path)
        _collect_terms(_normalized_observable_value(path, left), term_path, left_terms)
        _collect_terms(_normalized_observable_value(path, right), term_path, right_terms)
    return left_terms, right_terms


def _observable_deltas_from_leaves(
    leaves: Sequence[tuple[tuple[str, ...], Any, Any]],
) -> tuple[str, ...]:
    return tuple(
        ".".join(path)
        for path, left, right in leaves
        if canonical_json(_normalized_observable_value(path, left))
        != canonical_json(_normalized_observable_value(path, right))
    )


def machine_observable_deltas(chosen: dict[str, Any], rejected: dict[str, Any]) -> tuple[str, ...]:
    """Return changed paths from the reviewed, aligned observable projection."""

    return _observable_deltas_from_leaves(_common_arm_observable_leaves(chosen, rejected))


def _unicode_terms(value: str) -> tuple[str, ...]:
    """Tokenize words without turning unspaced Unicode into one atom.

    Compatibility decomposition keeps accented and unaccented spellings on
    the same lexical stem; combining marks do not manufacture independence.
    ASCII words stay intact. Other letters and digits are emitted as
    normalized code-point terms, so a one-character edit in unspaced CJK
    changes one term instead of replacing the entire rationale.
    """

    normalized = unicodedata.normalize("NFKD", value.casefold()).translate(_CONFUSABLE_ASCII)
    terms: list[str] = []
    ascii_word: list[str] = []

    def flush_ascii() -> None:
        if ascii_word:
            terms.append("".join(ascii_word))
            ascii_word.clear()

    for character in normalized:
        category = unicodedata.category(character)
        if unicodedata.combining(character) or category.startswith("M"):
            continue
        if category == "Cf":
            # Zero-width joiners, bidi controls, and other invisible format
            # marks must not split one visible word into distant fragments.
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


def _bounded_machine_identifier(value: str) -> str | None:
    """Return one Unicode-script identifier key, rejecting prose and controls."""

    normalized = unicodedata.normalize("NFKC", value)
    if not 1 <= len(normalized) <= 128 or not normalized[0].isalnum():
        return None
    scripts: set[str] = set()
    for character in normalized:
        if character in "_.:/-":
            continue
        if unicodedata.category(character).startswith("M"):
            # Marks may be required by the script, but the lexical skeleton
            # drops them so mark-only edits still cannot create a delta.
            continue
        if not character.isalnum():
            return None
        if character.isdecimal():
            # ASCII digits are script-neutral. Non-ASCII digits are visually
            # ambiguous in identifiers and are not needed by this contract.
            if not character.isascii():
                return None
            continue
        name = unicodedata.name(character, "")
        if not name:
            return None
        script = name.split(" ", 1)[0]
        if script.startswith(("BOPOMOFO", "CJK", "HANGUL", "HIRAGANA", "KATAKANA")):
            script = "EAST_ASIAN"
        scripts.add(script)
    if len(scripts) > 1:
        return None
    terms = "".join(_unicode_terms(normalized))
    return terms or None


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


def differs_only_by_gate_label(chosen: dict[str, Any], rejected: dict[str, Any]) -> bool:
    """Whether the sole contrastive change is a safety gate decision label."""

    chosen_surface = _behavior_surface(chosen)
    rejected_surface = _behavior_surface(rejected)
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
    """Return one arm's path-scoped, reviewed observable projection."""

    terms: Counter[str] = Counter()
    for field_name in MACHINE_OBSERVABLE_FIELDS:
        if field_name in arm:
            terms.update(_single_observable_terms(arm[field_name], (field_name,)))
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
    """Return distance over the same aligned projection used for deltas."""

    chosen_terms, rejected_terms = _observable_terms(
        _common_arm_observable_leaves(chosen, rejected)
    )
    return 1.0 - cosine_similarity(chosen_terms, rejected_terms)


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


def render_human(scan: ArmScan) -> str:
    summary = scan.summary
    lines = [
        f"Preference pairs: {summary['preference_pairs']}",
        f"Same-context: {summary['same_context_pairs']} ({summary['context_purity_pct']}%)",
        f"Two-session attested: {summary['two_session_pairs']}",
        f"Reservation-bound two-session: {summary['trusted_two_session_pairs']}",
        f"Min arm distance required: > {summary['min_arm_distance']}",
        f"Observed arm distance: {summary['observed_min_arm_distance']}"
        f" .. {summary['observed_max_arm_distance']}",
        f"Blocked: {summary['blocked_pairs']}",
    ]
    for decision in scan.decisions:
        location = f"{decision.source_path}:{decision.source_line}"
        record_id = decision.record_id or "<no-id>"
        verdict = "BLOCKED [" + ",".join(decision.reason_codes) + "]" if decision.blocked else "ok"
        lines.append(f"- {location} {record_id}: distance={decision.arm_distance} {verdict}")
    return "\n".join(lines)


def _validated_distance_floor(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"arm-distance floor must be numeric: {value!r}")
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value < 1.0:
        raise ValueError(f"arm-distance floor must be a finite value in [0, 1): {value!r}")
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


def diagnosis_filenames(round_number: int, count: int) -> tuple[str, ...]:
    """Return the transaction-derived contiguous diagnosis allowlist."""

    if type(round_number) is not int or round_number < 1:
        raise PreferenceArmsError("diagnosis round must be a positive integer")
    if type(count) is not int or count < 1:
        raise PreferenceArmsError("diagnosis count must be a positive integer")
    round_text = f"{round_number:02d}"
    return tuple(f"diagnosis-{index:02d}-r{round_text}.md" for index in range(1, count + 1))


def diagnosis_receipt_filename(round_number: int) -> str:
    """Return the one canonical receipt basename for a round."""

    if type(round_number) is not int or round_number < 1:
        raise PreferenceArmsError("diagnosis receipt round must be a positive integer")
    return f"diagnosis-handoff-receipt-r{round_number:02d}.json"


def _strict_json_object(payload: bytes, *, label: str) -> dict[str, Any]:
    """Decode one finite JSON object while rejecting duplicate keys."""

    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PreferenceArmsError(f"{label} is not valid UTF-8: {exc}") from exc

    def object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key {key!r}")
            result[key] = value
        return result

    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON constant {value}")

    try:
        value = json.loads(
            text,
            object_pairs_hook=object_pairs,
            parse_constant=reject_constant,
        )
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise PreferenceArmsError(f"{label} is not strict JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise PreferenceArmsError(f"{label} must be a JSON object")
    return value


def _diagnosis_fenced_object(lines: list[str], *, label: str) -> dict[str, Any]:
    """Decode a section that contains exactly one fenced JSON object."""

    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if len(lines) < 3 or lines[0] != "```json" or lines[-1] != "```":
        raise PreferenceArmsError(f"{label} must contain exactly one fenced JSON object")
    if any(line.startswith("```") for line in lines[1:-1]):
        raise PreferenceArmsError(f"{label} contains an extra code fence")
    payload = "\n".join(lines[1:-1]).encode("utf-8")
    return _strict_json_object(payload, label=label)


def _validate_shared_context_tree(
    value: Any,
    *,
    label: str,
    depth: int = 0,
    budget: list[int] | None = None,
) -> None:
    """Reject nested payload channels inside the two allowed context objects."""

    if budget is None:
        budget = [0]
    budget[0] += 1
    if budget[0] > MAX_DIAGNOSIS_NODES:
        raise PreferenceArmsError(f"{label} exceeds the shared-context node limit")
    if depth > MAX_DIAGNOSIS_DEPTH:
        raise PreferenceArmsError(f"{label} exceeds the shared-context depth limit")
    if isinstance(value, dict):
        forbidden = sorted(key for key in value if _is_rejected_trajectory_key(key))
        if forbidden:
            raise PreferenceArmsError(
                f"{label} contains rejected-trajectory keys: " + ", ".join(forbidden)
            )
        for item in value.values():
            _validate_shared_context_tree(
                item,
                label=label,
                depth=depth + 1,
                budget=budget,
            )
    elif isinstance(value, list):
        for item in value:
            _validate_shared_context_tree(
                item,
                label=label,
                depth=depth + 1,
                budget=budget,
            )
    elif isinstance(value, str) and (
        _text_contains_rejected_trajectory_mapping(value)
        or _ENCODED_BLOB_RE.search(value)
        or "data:" in value.casefold()
        or "%7b" in value.casefold()
        or "%7d" in value.casefold()
    ):
        raise PreferenceArmsError(f"{label} contains an encoded or serialized payload string")
    elif type(value) is float and not math.isfinite(value):
        raise PreferenceArmsError(f"{label} contains a non-finite number")


def validate_diagnosis_document(payload: bytes, *, label: str) -> dict[str, Any]:
    """Validate the bounded diagnosis bridge without returning its prose.

    The bridge may carry only one shared-context object, five bounded prose
    sections, and one target-delta object. It cannot carry another code block,
    heading, or serialized trajectory-key mapping that would expose Session B
    to the rejected gate, execution, outcome, or reward payload.
    """

    if len(payload) > MAX_DIAGNOSIS_BYTES:
        raise PreferenceArmsError(f"{label} exceeds the {MAX_DIAGNOSIS_BYTES}-byte diagnosis limit")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PreferenceArmsError(f"{label} is not valid UTF-8: {exc}") from exc
    text = text.replace("\r\n", "\n")
    if "\r" in text:
        raise PreferenceArmsError(f"{label} contains an unsupported bare carriage return")
    if any(
        unicodedata.category(character) == "Cc" and character not in "\t\n" for character in text
    ):
        raise PreferenceArmsError(f"{label} contains an unsupported control character")
    lines = text.split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines or lines[0] != "# Diagnosis":
        raise PreferenceArmsError(f"{label} must start with '# Diagnosis'")

    expected_headings = [f"## {name}" for name in DIAGNOSIS_SECTIONS]
    observed_headings = [line for line in lines[1:] if line.startswith("#")]
    if observed_headings != expected_headings:
        raise PreferenceArmsError(
            f"{label} headings must be exactly " + ", ".join(expected_headings)
        )
    positions = [lines.index(heading) for heading in expected_headings]
    sections = {
        name: lines[start + 1 : positions[index + 1] if index + 1 < len(positions) else len(lines)]
        for index, (name, start) in enumerate(zip(DIAGNOSIS_SECTIONS, positions, strict=True))
    }

    context = _diagnosis_fenced_object(
        list(sections["Shared context"]),
        label=f"{label} shared context",
    )
    if set(context) != {"state", "proposed_action"}:
        raise PreferenceArmsError(
            f"{label} shared context keys must be exactly state and proposed_action"
        )
    if not isinstance(context["state"], dict) or not isinstance(context["proposed_action"], dict):
        raise PreferenceArmsError(f"{label} shared context values must be JSON objects")
    _validate_shared_context_tree(context, label=f"{label} shared context")

    narratives: dict[str, str] = {}
    for name in DIAGNOSIS_SECTIONS[1:-1]:
        narrative = "\n".join(sections[name]).strip()
        if not narrative:
            raise PreferenceArmsError(f"{label} section {name!r} is empty")
        if len(narrative) > MAX_DIAGNOSIS_NARRATIVE_CHARS:
            raise PreferenceArmsError(f"{label} section {name!r} exceeds the narrative limit")
        if any(len(line) > MAX_DIAGNOSIS_LINE_CHARS for line in narrative.splitlines()):
            raise PreferenceArmsError(f"{label} section {name!r} has an oversized line")
        lowered = narrative.casefold()
        if "```" in narrative or "~~~" in narrative:
            raise PreferenceArmsError(f"{label} section {name!r} contains a code fence")
        if "{" in narrative or "}" in narrative:
            raise PreferenceArmsError(f"{label} section {name!r} contains object syntax")
        if "<!--" in narrative or re.search(r"</?[A-Za-z][^>]*>", narrative):
            raise PreferenceArmsError(f"{label} section {name!r} contains raw HTML")
        if any(re.fullmatch(r"\s*\|.*\|\s*", line) is not None for line in narrative.splitlines()):
            raise PreferenceArmsError(f"{label} section {name!r} contains a Markdown table")
        if (
            _text_contains_rejected_trajectory_mapping(narrative)
            or _ENCODED_BLOB_RE.search(narrative)
            or "data:" in lowered
            or "%7b" in lowered
            or "%7d" in lowered
            or re.search(r"\bbase64\b", lowered)
        ):
            raise PreferenceArmsError(
                f"{label} section {name!r} contains an encoded or serialized payload"
            )
        narratives[name] = narrative

    target = _diagnosis_fenced_object(
        list(sections["Target reward delta"]),
        label=f"{label} target reward delta",
    )
    if set(target) != {"per_component", "total"} or not isinstance(target["per_component"], dict):
        raise PreferenceArmsError(
            f"{label} target reward delta must contain per_component and total only"
        )
    components = target["per_component"]
    if not components or len(components) > MAX_DIAGNOSIS_COMPONENTS:
        raise PreferenceArmsError(
            f"{label} target reward delta must have 1-{MAX_DIAGNOSIS_COMPONENTS} components"
        )
    for key, value in components.items():
        if (
            not isinstance(key, str)
            or _COMPONENT_SLUG_RE.fullmatch(key) is None
            or isinstance(value, bool)
            or not isinstance(value, (int, float))
            or (type(value) is float and not math.isfinite(value))
        ):
            raise PreferenceArmsError(
                f"{label} target reward component {key!r} must be a finite number"
            )
    total = target["total"]
    if (
        isinstance(total, bool)
        or not isinstance(total, (int, float))
        or (type(total) is float and not math.isfinite(total))
    ):
        raise PreferenceArmsError(f"{label} target reward total must be a finite number")
    try:
        numeric_total = float(total)
        component_sum = math.fsum(float(value) for value in components.values())
    except OverflowError as exc:
        raise PreferenceArmsError(
            f"{label} target reward values exceed the supported numeric range"
        ) from exc
    if not math.isfinite(numeric_total) or not math.isfinite(component_sum):
        raise PreferenceArmsError(
            f"{label} target reward values exceed the supported numeric range"
        )
    if numeric_total <= 0:
        raise PreferenceArmsError(f"{label} target reward total must be positive")
    if not math.isclose(numeric_total, component_sum, rel_tol=0.0, abs_tol=1e-6):
        raise PreferenceArmsError(f"{label} target reward total does not equal the component sum")
    return {"shared_context": context, "target_reward_delta": target}


def _read_regular_artifact(
    root: Path,
    name: str,
    *,
    label: str,
    max_bytes: int | None = None,
) -> bytes:
    root_fd = -1
    try:
        root_fd = _open_canonical_directory(root, label=f"{label} root")
        return _read_regular_artifact_from_directory(
            root_fd,
            name,
            label=label,
            max_bytes=max_bytes,
        )
    finally:
        if root_fd >= 0:
            os.close(root_fd)


def _read_regular_artifact_from_directory(
    root_fd: int,
    name: str,
    *,
    label: str,
    max_bytes: int | None = None,
) -> bytes:
    """Read one regular artifact relative to an already-bound directory."""

    if not isinstance(name, str) or Path(name).name != name:
        raise PreferenceArmsError(f"{label} name is not a safe basename: {name!r}")
    file_fd = -1
    try:
        file_stat = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
        if stat.S_ISLNK(file_stat.st_mode) or not stat.S_ISREG(file_stat.st_mode):
            raise PreferenceArmsError(f"{label} is not a real file: {name}")
        if max_bytes is not None and file_stat.st_size > max_bytes:
            raise PreferenceArmsError(f"{label} exceeds the {max_bytes}-byte limit: {name}")
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        file_fd = os.open(name, flags, dir_fd=root_fd)
        opened_stat = os.fstat(file_fd)
        if not stat.S_ISREG(opened_stat.st_mode):
            raise PreferenceArmsError(f"{label} is not a real file: {name}")
        if not _same_file_identity(file_stat, opened_stat):
            raise PreferenceArmsError(f"{label} changed while it was opened: {name}")
        if max_bytes is not None and opened_stat.st_size > max_bytes:
            raise PreferenceArmsError(f"{label} exceeds the {max_bytes}-byte limit: {name}")
        with os.fdopen(file_fd, "rb") as handle:
            file_fd = -1
            payload = handle.read(None if max_bytes is None else max_bytes + 1)
        if max_bytes is not None and len(payload) > max_bytes:
            raise PreferenceArmsError(f"{label} exceeds the {max_bytes}-byte limit: {name}")
        return payload
    except PreferenceArmsError:
        raise
    except OSError as exc:
        raise PreferenceArmsError(f"{label} cannot be read: {name}: {exc}") from exc
    finally:
        if file_fd >= 0:
            os.close(file_fd)


def _same_file_identity(left: os.stat_result, right: os.stat_result) -> bool:
    return (left.st_dev, left.st_ino) == (right.st_dev, right.st_ino)


def _open_canonical_directory(root: Path, *, label: str) -> int:
    """Open one canonical directory and bind callers to its verified inode."""

    root = Path(root)
    try:
        canonical_root = root.resolve(strict=True)
        path_stat = root.lstat()
    except OSError as exc:
        raise PreferenceArmsError(f"{label} cannot be resolved: {root}: {exc}") from exc
    if canonical_root != root:
        raise PreferenceArmsError(f"{label} is not canonical: {root}")
    if stat.S_ISLNK(path_stat.st_mode) or not stat.S_ISDIR(path_stat.st_mode):
        raise PreferenceArmsError(f"{label} is not a real directory: {root}")
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    directory_fd = -1
    try:
        directory_fd = os.open(root, flags)
        opened_stat = os.fstat(directory_fd)
        if not stat.S_ISDIR(opened_stat.st_mode) or not _same_file_identity(path_stat, opened_stat):
            raise PreferenceArmsError(f"{label} changed while it was opened: {root}")
        return directory_fd
    except BaseException:
        if directory_fd >= 0:
            os.close(directory_fd)
        raise


def _require_open_directory_identity(root: Path, root_fd: int, *, label: str) -> None:
    """Require the canonical pathname to still name the bound directory."""

    try:
        current_stat = Path(root).lstat()
        opened_stat = os.fstat(root_fd)
    except OSError as exc:
        raise PreferenceArmsError(f"{label} changed while open: {root}: {exc}") from exc
    if (
        stat.S_ISLNK(current_stat.st_mode)
        or not stat.S_ISDIR(current_stat.st_mode)
        or not _same_file_identity(current_stat, opened_stat)
    ):
        raise PreferenceArmsError(f"{label} changed while open: {root}")


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


def _session_b_outputs(names: Sequence[str], round_text: str) -> list[str]:
    forbidden_names = {
        f"batch-r{round_text}.jsonl",
        f"NOTES-r{round_text}.md",
    }
    chosen_re = re.compile(rf"chosen-[A-Za-z0-9._-]+-r{re.escape(round_text)}\.json\Z")
    return sorted(name for name in names if name in forbidden_names or chosen_re.fullmatch(name))


def validate_diagnosis_handoff_receipt(
    artifact_dir: Path,
    *,
    factory: str,
    round_number: int,
    staging_dir: Path,
    reservation_token: str,
    expected_count: int,
) -> dict[str, Any]:
    """Validate one persisted receipt against captured or committed bytes."""

    root = Path(artifact_dir)
    if not root.is_dir() or root.is_symlink():
        raise PreferenceArmsError(f"diagnosis artifact root is unsafe: {root}")
    expected_names = diagnosis_filenames(round_number, expected_count)
    receipt_name = diagnosis_receipt_filename(round_number)
    allowed_diagnosis_names = {*expected_names, receipt_name}
    round_suffix = f"-r{round_number:02d}."
    try:
        diagnosis_named = {
            path.name
            for path in root.iterdir()
            if path.name.startswith("diagnosis-") and round_suffix in path.name
        }
    except OSError as exc:
        raise PreferenceArmsError(
            f"diagnosis artifact root cannot be inspected: {root}: {exc}"
        ) from exc
    unexpected = sorted(diagnosis_named - allowed_diagnosis_names)
    missing = sorted(allowed_diagnosis_names - diagnosis_named)
    if unexpected:
        raise PreferenceArmsError("unexpected diagnosis artifact(s): " + ", ".join(unexpected))
    if missing:
        raise PreferenceArmsError("missing diagnosis artifact(s): " + ", ".join(missing))

    receipt_bytes = _read_regular_artifact(
        root,
        receipt_name,
        label="diagnosis receipt",
        max_bytes=MAX_DIAGNOSIS_BYTES,
    )
    receipt = _strict_json_object(receipt_bytes, label="diagnosis receipt")
    required_keys = {
        "version",
        "factory",
        "round",
        "staging_dir",
        "reservation_token",
        "diagnosis_files",
    }
    if set(receipt) != required_keys:
        raise PreferenceArmsError(
            "diagnosis receipt keys must be exactly " + ", ".join(sorted(required_keys))
        )
    if type(receipt["version"]) is not int or receipt["version"] != HANDOFF_RECEIPT_VERSION:
        raise PreferenceArmsError("diagnosis receipt has an unsupported version")
    if receipt["factory"] != factory:
        raise PreferenceArmsError("diagnosis receipt factory does not match the reservation")
    if type(receipt["round"]) is not int or receipt["round"] != round_number:
        raise PreferenceArmsError("diagnosis receipt round does not match the reservation")
    if receipt["staging_dir"] != str(staging_dir):
        raise PreferenceArmsError(
            "diagnosis receipt staging directory does not match the reservation"
        )
    if (
        not isinstance(reservation_token, str)
        or re.fullmatch(r"[0-9a-f]{32}", reservation_token) is None
        or receipt["reservation_token"] != reservation_token
    ):
        raise PreferenceArmsError("diagnosis receipt token does not match the reservation")

    entries = receipt["diagnosis_files"]
    if not isinstance(entries, list) or len(entries) != expected_count:
        raise PreferenceArmsError("diagnosis receipt has the wrong number of file entries")
    validated_entries: list[tuple[str, int, str]] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or set(entry) != {"name", "bytes", "sha256"}:
            raise PreferenceArmsError(f"diagnosis receipt entry {index + 1} has invalid keys")
        name = entry["name"]
        byte_count = entry["bytes"]
        digest = entry["sha256"]
        expected_name = expected_names[index]
        if not isinstance(name, str) or Path(name).name != name or name != expected_name:
            raise PreferenceArmsError(f"diagnosis receipt entry {index + 1} has invalid name")
        if type(byte_count) is not int or byte_count < 1:
            raise PreferenceArmsError(f"diagnosis receipt entry {name!r} has invalid byte count")
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise PreferenceArmsError(f"diagnosis receipt entry {name!r} has invalid SHA-256")
        validated_entries.append((name, byte_count, digest))

    for name, byte_count, digest in validated_entries:
        payload = _read_regular_artifact(
            root,
            name,
            label="diagnosis file",
            max_bytes=MAX_DIAGNOSIS_BYTES,
        )
        validate_diagnosis_document(payload, label=f"diagnosis file {name}")
        if len(payload) != byte_count:
            raise PreferenceArmsError(f"diagnosis file byte count does not match receipt: {name}")
        if hashlib.sha256(payload).hexdigest() != digest:
            raise PreferenceArmsError(f"diagnosis file SHA-256 does not match receipt: {name}")

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
