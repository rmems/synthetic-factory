"""Training-view leak check for VSET records.

Keys are folded so renamed hidden-suite fields match. A string leaks only
when it matches a pack file ``tests/hidden_*.py``: the sha256 of those
bytes, the file text, or a line that appears in that file and not in the
pack's visible tests. Ordinary ``def test_`` code is not a marker.
"""

from __future__ import annotations

import hashlib
import io
import re
import sys
import tokenize
import unicodedata
from pathlib import Path
from typing import Any

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_training_view")
    from .curate_coding import contains_hidden_reasoning_key
    from .vset_constants import (
        ERR_PAYLOAD_INVALID,
        VSetValidationError,
        normalize_identity,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_training_view"
    )
    from curate_coding import contains_hidden_reasoning_key
    from vset_constants import (
        ERR_PAYLOAD_INVALID,
        VSetValidationError,
        normalize_identity,
    )


_TRAINING_VIEW_LEAKS = frozenset(
    {
        "hidden_tests",
        "hidden_suite",
        "reference_tests",
        "reference_suite",
        "private_tests",
        "oracle_suite",
        "grading_tests",
        "tests_source",
        "oracle",
        "payload",
        "patch",
        "solver",
        "solver_run_id",
    }
)

# The whole hidden file must be at least this long before it is a substring.
# A shorter file is identified by its sha256 only.
_MIN_HIDDEN_SNIPPET = 64
# Lines shorter than this are shared boilerplate (``import unittest``).
_MIN_DISTINCTIVE_LINE = 24

_EMPTY_DIGESTS: frozenset[str] = frozenset()
_LEAK_MESSAGE = "training_view must not carry hidden suites, oracle, payload, patch, or solver"


def _boundary_before(previous: str, char: str, following: str) -> bool:
    """A camel boundary, including non-ASCII capitals such as Cyrillic ``Т``."""

    if not previous or not char.isupper():
        return False
    if previous.islower():
        return True
    if previous.isdigit():
        return True
    if not previous.isupper():
        return False
    return following.islower()


def _split_camel_boundaries(text: str) -> str:
    chars: list[str] = []
    for index, char in enumerate(text):
        previous = text[index - 1] if index else ""
        following = text[index + 1] if index + 1 < len(text) else ""
        if _boundary_before(previous, char, following):
            chars.append("_")
        chars.append(char)
    return "".join(chars)


def _training_view_key(key: Any) -> str:
    """Fold case, separators, camel-case, and lookalikes so keys match.

    Width variants are normalized before the camel split, so a fullwidth
    ``Ｔ`` becomes ``T``. The split uses ``str.isupper`` so a Cyrillic
    capital also starts a word. Separators become underscores before the
    identity fold, which deletes whitespace rather than keeping it.
    """

    text = unicodedata.normalize("NFKC", str(key))
    split = _split_camel_boundaries(text)
    separated = re.sub(r"[^\w]+", "_", split, flags=re.UNICODE)
    folded = normalize_identity(separated)
    return re.sub(r"[^a-z0-9]+", "_", folded).strip("_")


def _normalize_newlines(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n")


def _is_hidden_suite_path(path: Path) -> bool:
    if not path.is_file():
        return False
    if not path.name.startswith("hidden_"):
        return False
    return path.suffix == ".py"


def _is_visible_test_path(path: Path) -> bool:
    if not path.is_file():
        return False
    if path.suffix != ".py":
        return False
    return not path.name.startswith("hidden_")


def _tests_directory(pack_dir: Path | None) -> Path | None:
    if pack_dir is None:
        return None
    return Path(pack_dir) / "tests"


def _usable_tests_directory(pack_dir: Path | None) -> Path | None:
    tests = _tests_directory(pack_dir)
    if tests is None:
        return None
    if tests.is_dir():
        return tests
    return None


def _read_suite_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise VSetValidationError(
            ERR_PAYLOAD_INVALID, f"unreadable hidden suite {path.name}: {exc}"
        ) from exc


def _decode_suite_source(raw: bytes, name: str) -> str:
    try:
        encoding = tokenize.detect_encoding(io.BytesIO(raw).readline)[0]
        return raw.decode(encoding)
    except (SyntaxError, UnicodeError, LookupError) as exc:
        raise VSetValidationError(
            ERR_PAYLOAD_INVALID, f"undecodable hidden suite {name}: {exc}"
        ) from exc


def _suite_text(path: Path) -> str:
    return _normalize_newlines(_decode_suite_source(_read_suite_bytes(path), path.name))


def _add_stripped_lines(source: str, lines: set[str]) -> None:
    for line in source.splitlines():
        stripped = line.strip()
        if stripped:
            lines.add(stripped)


def _visible_lines(tests: Path) -> set[str]:
    lines: set[str] = set()
    for path in sorted(tests.iterdir()):
        if _is_visible_test_path(path):
            _add_stripped_lines(_suite_text(path), lines)
    return lines


def _append_source_snippets(source: str, visible: set[str], snippets: list[str]) -> None:
    stripped = source.strip()
    if len(stripped) >= _MIN_HIDDEN_SNIPPET:
        snippets.append(stripped)
    for line in source.splitlines():
        text = line.strip()
        if len(text) < _MIN_DISTINCTIVE_LINE:
            continue
        if text in visible:
            continue
        snippets.append(text)


def _append_hidden_file(
    path: Path,
    visible: set[str],
    digests: list[str],
    snippets: list[str],
) -> None:
    raw = _read_suite_bytes(path)
    digests.append(hashlib.sha256(raw).hexdigest())
    text = _normalize_newlines(_decode_suite_source(raw, path.name))
    _append_source_snippets(text, visible, snippets)


def _hidden_suite_pins(
    pack_dir: Path | None,
) -> tuple[frozenset[str], tuple[str, ...], list[VSetValidationError]]:
    tests = _usable_tests_directory(pack_dir)
    if tests is None:
        return _EMPTY_DIGESTS, (), []
    digests: list[str] = []
    snippets: list[str] = []
    try:
        visible = _visible_lines(tests)
        for path in sorted(tests.iterdir()):
            if not _is_hidden_suite_path(path):
                continue
            _append_hidden_file(path, visible, digests, snippets)
    except VSetValidationError as exc:
        return _EMPTY_DIGESTS, (), [exc]
    return frozenset(digests), tuple(snippets), []


def _digest_leaks(value: str, digests: frozenset[str]) -> bool:
    if hashlib.sha256(value.encode("utf-8")).hexdigest() in digests:
        return True
    return any(digest in value for digest in digests)


def _text_matches_hidden(
    value: str, digests: frozenset[str], snippets: tuple[str, ...]
) -> bool:
    if _digest_leaks(value, digests):
        return True
    folded = _normalize_newlines(value)
    return any(snippet in folded for snippet in snippets)


def _key_leaks(key: Any, digests: frozenset[str], snippets: tuple[str, ...]) -> bool:
    if _training_view_key(key) in _TRAINING_VIEW_LEAKS:
        return True
    return isinstance(key, str) and _text_matches_hidden(key, digests, snippets)


def _mapping_leaks(
    value: dict[str, Any], digests: frozenset[str], snippets: tuple[str, ...]
) -> bool:
    if any(_key_leaks(key, digests, snippets) for key in value):
        return True
    return any(_training_view_leaks(item, digests, snippets) for item in value.values())


def _training_view_leaks(
    value: Any, digests: frozenset[str], snippets: tuple[str, ...]
) -> bool:
    """Walk dicts and lists. Keys are case-insensitive; strings match the pack."""
    if isinstance(value, str):
        return _text_matches_hidden(value, digests, snippets)
    if isinstance(value, dict):
        return _mapping_leaks(value, digests, snippets)
    if isinstance(value, list):
        return any(_training_view_leaks(item, digests, snippets) for item in value)
    return False


def _leak_error() -> VSetValidationError:
    return VSetValidationError("vset.hidden_reasoning_in_training_view", _LEAK_MESSAGE)


def _training_view_errors(
    training_view: Any, pack_dir: Path | None = None
) -> list[VSetValidationError]:
    if not isinstance(training_view, dict):
        return [
            VSetValidationError(
                "vset.hidden_reasoning_in_training_view",
                "training_view is required and must be an object",
            )
        ]
    digests, snippets, read_errors = _hidden_suite_pins(pack_dir)
    if read_errors:
        return read_errors
    if contains_hidden_reasoning_key(training_view):
        return [_leak_error()]
    if _training_view_leaks(training_view, digests, snippets):
        return [_leak_error()]
    return []


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
