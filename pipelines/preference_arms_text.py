#!/usr/bin/env python3
"""Lexical primitives and the gate's error types.

Leaf module of the preference-arm gate: it depends on no other
``preference_arms_*`` module.
"""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from typing import Any
import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from curate_preferences import canonical_json  # noqa: E402




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


_ENCODED_BLOB_RE = re.compile(r"\b(?:[0-9a-fA-F]{256,}|[A-Za-z0-9_-]{256,}={0,2})\b")


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


class PreferenceArmsError(RuntimeError):
    """Raised when a source cannot be read as preference JSONL."""


class ListAlignmentError(PreferenceArmsError):
    """Raised when unordered list evidence exceeds the bounded matcher."""


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
