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


# A mapping label in prose may be spelled with spaces between its words
# (``executed action:``) and may trail an ordinary sentence, so the whole
# phrase in front of the separator is captured and its trailing word windows
# are compared. Quoted keys are handled by the serialized pattern above.
_NARRATIVE_MAPPING_KEY_RE = re.compile(r"([^\n:=\"'`{}\[\],]{1,128})\s*[:=]")


#: Longest key phrase in :data:`_REJECTED_TRAJECTORY_KEYS`, plus one word of
#: slack, bounding how far back a trailing window is taken.
_MAX_LABEL_PHRASE_WORDS = 3


_WORD_RE = re.compile(r"[^\W_]+")


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
    """Whether one structural JSON key names a rejected-trajectory field."""

    if _has_ambiguous_script(value):
        return True
    normalized = _normalized_payload_key(value)
    return normalized.replace("_", "") in _REJECTED_TRAJECTORY_KEY_SHAPES


def _label_phrase_shapes(normalized: str) -> tuple[str, ...]:
    """Collapsed shapes of a label's trailing word windows.

    Structural keys are matched whole, but a label written in prose can carry
    an ordinary sentence in front of it, so the key phrase is looked for at
    the end of the label rather than across the whole of it.
    """

    words = [word for word in normalized.split("_") if word]
    first = max(0, len(words) - _MAX_LABEL_PHRASE_WORDS)
    return tuple("".join(words[start:]) for start in range(first, len(words)))


def _is_rejected_trajectory_label(value: str) -> bool:
    """Whether a mapping label written in prose names a rejected field."""

    if _has_ambiguous_script(value):
        return True
    shapes = _label_phrase_shapes(_normalized_payload_key(value))
    return any(shape in _REJECTED_TRAJECTORY_KEY_SHAPES for shape in shapes)


def _text_contains_rejected_trajectory_mapping(value: str) -> bool:
    """Reject ASCII, spaced, and homoglyph YAML/JSON mapping keys in prose."""

    # Compatibility spellings are folded first so a fullwidth colon or quote
    # is the delimiter it renders as before either pattern is applied.
    compatible = unicodedata.normalize("NFKC", value)
    if _SERIALIZED_TRAJECTORY_KEY_RE.search(compatible):
        return True
    return any(
        _is_rejected_trajectory_label(match.group(1))
        for match in _NARRATIVE_MAPPING_KEY_RE.finditer(compatible)
    )


def _is_ignorable_lexical_character(character: str) -> bool:
    """Report characters that a word neither starts, ends, nor breaks on."""

    category = unicodedata.category(character)
    if unicodedata.combining(character) or category.startswith("M"):
        return True
    # Zero-width joiners, bidi controls, and other invisible format
    # marks must not split one visible word into distant fragments.
    return category == "Cf"


def _is_ascii_word_character(character: str) -> bool:
    """Report characters that extend the ASCII word being accumulated."""

    return character.isascii() and character.isalnum()


def _flush_ascii_word(ascii_word: list[str], terms: list[str]) -> None:
    """Emit the pending ASCII word, if there is one, and begin the next."""

    if ascii_word:
        terms.append("".join(ascii_word))
        ascii_word.clear()


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
    for character in normalized:
        if _is_ignorable_lexical_character(character):
            continue
        if _is_ascii_word_character(character):
            ascii_word.append(character)
            continue
        _flush_ascii_word(ascii_word, terms)
        if character.isalnum():
            terms.append(character)
    _flush_ascii_word(ascii_word, terms)
    return tuple(terms)


def _has_bounded_identifier_shape(normalized: str) -> bool:
    """Report the length and leading-character shape an identifier must have."""

    if not 1 <= len(normalized) <= 128:
        return False
    return normalized[0].isalnum()


def _is_scriptless_identifier_character(character: str) -> bool:
    """Report identifier characters that carry no script of their own."""

    if character in "_.:/-":
        return True
    # Marks may be required by the script, but the lexical skeleton
    # drops them so mark-only edits still cannot create a delta.
    return unicodedata.category(character).startswith("M")


def _identifier_digit_script(character: str) -> str | None:
    """Classify a decimal digit as script-neutral, or reject the identifier."""

    # ASCII digits are script-neutral. Non-ASCII digits are visually
    # ambiguous in identifiers and are not needed by this contract.
    if not character.isascii():
        return None
    return ""


def _named_character_script(character: str) -> str | None:
    """Read the script from a character's Unicode name, folding East Asian."""

    name = unicodedata.name(character, "")
    if not name:
        return None
    script = name.split(" ", 1)[0]
    if script.startswith(("BOPOMOFO", "CJK", "HANGUL", "HIRAGANA", "KATAKANA")):
        return "EAST_ASIAN"
    return script


def _identifier_character_script(character: str) -> str | None:
    """Return one character's script, ``""`` for none, ``None`` to reject."""

    if _is_scriptless_identifier_character(character):
        return ""
    if not character.isalnum():
        return None
    if character.isdecimal():
        return _identifier_digit_script(character)
    return _named_character_script(character)


def _letter_script(character: str) -> str:
    """One letter's script, East Asian folded, ``""`` for anything else."""

    if not character.isalpha():
        return ""
    return _named_character_script(character) or ""


def _has_ambiguous_script(value: str) -> bool:
    """Whether one word draws its letters from more than one script.

    A hand-maintained lookalike table can never cover the whole Unicode
    confusables set, so a word whose skeleton is ambiguous is refused rather
    than normalized. Mixing scripts inside a single word is the shape every
    cross-script homoglyph substitution takes, and it is what this reports;
    wholly non-Latin words are single-script and pass through untouched.
    """

    normalized = unicodedata.normalize("NFKC", value)
    for word in _WORD_RE.findall(normalized):
        scripts = {script for script in map(_letter_script, word) if script}
        if len(scripts) > 1:
            return True
    return False


def _identifier_scripts(normalized: str) -> set[str] | None:
    """Collect the scripts an identifier draws on, or ``None`` to reject it."""

    scripts: set[str] = set()
    for character in normalized:
        script = _identifier_character_script(character)
        if script is None:
            return None
        if script:
            scripts.add(script)
    return scripts


def _bounded_identifier_script(value: str) -> str | None:
    """The one script an identifier draws on, ``""`` for none, ``None`` to reject.

    Callers compare this across the two arms: a machine identifier that swaps
    script between them is a cross-script lookalike substitution, never a
    behavioral change, whether or not the folding table happens to list it.
    """

    normalized = unicodedata.normalize("NFKC", value)
    if not _has_bounded_identifier_shape(normalized):
        return None
    scripts = _identifier_scripts(normalized)
    if scripts is None or len(scripts) > 1:
        return None
    return next(iter(scripts), "")


def _bounded_machine_identifier(value: str) -> str | None:
    """Return one Unicode-script identifier key, rejecting prose and controls."""

    if _bounded_identifier_script(value) is None:
        return None
    terms = "".join(_unicode_terms(unicodedata.normalize("NFKC", value)))
    return terms or None


def _collect_mapping_terms(value: dict[Any, Any], path: str, terms: Counter[str]) -> None:
    """Walk a mapping in key order so the traversal is deterministic."""

    for key in sorted(value):
        _collect_terms(value[key], f"{path}.{key}", terms)


def _collect_sequence_terms(value: list[Any], path: str, terms: Counter[str]) -> None:
    """Walk a list under one shared path."""

    # Position-insensitive: a reordered list is not a different arm.
    for item in value:
        _collect_terms(item, f"{path}[]", terms)


def _collect_word_terms(value: str, path: str, terms: Counter[str]) -> bool:
    """Count a string's words, reporting whether it had any."""

    words = _unicode_terms(value)
    for word in words:
        terms[f"{path}:{word}"] += 1
    return bool(words)


def _collect_terms(value: Any, path: str, terms: Counter[str]) -> None:
    if isinstance(value, dict):
        _collect_mapping_terms(value, path, terms)
        return
    if isinstance(value, list):
        _collect_sequence_terms(value, path, terms)
        return
    if isinstance(value, str) and _collect_word_terms(value, path, terms):
        return
    # Non-strings (and strings with no word characters) stay atomic so that
    # 0.2 and -0.2, or true and false, are never the same term.
    terms[f"{path}={canonical_json(value)}"] += 1


#: Two writers describing one incident reuse its vocabulary; they do not
#: reuse a twelve-word run of it. Below the lower bound a shared run is short
#: enough to be ordinary phrasing, so no claim is made either way.
_COPIED_PHRASE_WORDS = 12
_MIN_COPIED_PHRASE_WORDS = 6


def _phrase_shingles(words: tuple[str, ...], size: int) -> set[tuple[str, ...]]:
    """Every contiguous run of ``size`` normalized words in a text."""

    return {tuple(words[start : start + size]) for start in range(len(words) - size + 1)}


def shares_copied_phrasing(left: str, right: str) -> bool:
    """Whether two texts share a word run long enough to be a copy.

    The comparison runs on the same normalized terms the arm metric uses, so
    casing, accents, and homoglyph spellings cannot disguise a lift. A text
    shorter than the full run is compared at its own length, which catches a
    one-line rationale taken whole without letting a short stock phrase read
    as evidence of copying.
    """

    left_words = _unicode_terms(left)
    right_words = _unicode_terms(right)
    size = min(_COPIED_PHRASE_WORDS, len(left_words), len(right_words))
    if size < _MIN_COPIED_PHRASE_WORDS:
        return False
    return bool(_phrase_shingles(left_words, size) & _phrase_shingles(right_words, size))


def _term_vector_norm(vector: Counter[str]) -> float:
    """Euclidean norm of one term-frequency vector."""

    return math.sqrt(sum(count * count for count in vector.values()))


def _degenerate_cosine_similarity(left_norm: float, right_norm: float) -> float:
    """Score a pair where at least one surface carries no terms at all."""

    # An empty surface is degenerate, not distant. Callers flag it.
    return 1.0 if left_norm == right_norm else 0.0


def _term_vector_dot(left: Counter[str], right: Counter[str]) -> float:
    """Dot product of two term-frequency vectors, iterating the smaller one."""

    smaller, larger = (left, right) if len(left) <= len(right) else (right, left)
    return sum(count * larger[term] for term, count in smaller.items())


def cosine_similarity(left: Counter[str], right: Counter[str]) -> float:
    """Cosine similarity of two term-frequency vectors, clamped to [0, 1]."""

    left_norm = _term_vector_norm(left)
    right_norm = _term_vector_norm(right)
    if not left_norm or not right_norm:
        return _degenerate_cosine_similarity(left_norm, right_norm)
    dot = _term_vector_dot(left, right)
    # Clamp and round: identical vectors must land on exactly 1.0 rather than
    # 1 - 2e-16, and no decision here turns on the twelfth decimal.
    return round(max(0.0, min(1.0, dot / (left_norm * right_norm))), 12)
