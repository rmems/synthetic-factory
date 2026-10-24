"""Training-view leak check for VSET records.

Keys are folded so renamed hidden-suite fields match. A string leaks only
when it matches hidden-suite content: each ``tests/hidden_*.py`` file, and
each Python file the record lists in ``oracle.hidden_tests``. The match is
the sha256 of those bytes, the file text, or a named line (``def test_``
or ``class ``) that the pack's other tests do not share. Ordinary
``def test_`` code is not a marker.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import Any

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_training_view")
    from .curate_coding import contains_hidden_reasoning_key
    from .vset_constants import VSetValidationError
    from .vset_training_view_fold import TRAINING_VIEW_LEAKS, training_view_key
    from .vset_training_view_source import (
        append_source_snippets,
        file_digest,
        normalize_newlines,
        suite_text,
        visible_lines,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_training_view"
    )
    from curate_coding import contains_hidden_reasoning_key
    from vset_constants import VSetValidationError
    from vset_training_view_fold import TRAINING_VIEW_LEAKS, training_view_key
    from vset_training_view_source import (
        append_source_snippets,
        file_digest,
        normalize_newlines,
        suite_text,
        visible_lines,
    )


_EMPTY_DIGESTS: frozenset[str] = frozenset()
_LEAK_MESSAGE = "training_view must not carry hidden suites, oracle, payload, patch, or solver"


def _is_hidden_filename(path: Path) -> bool:
    if not path.is_file():
        return False
    if not path.name.startswith("hidden_"):
        return False
    return path.suffix == ".py"


def _tests_directory(pack_dir: Path) -> Path | None:
    tests = pack_dir / "tests"
    if tests.is_dir():
        return tests
    return None


def _stays_in_pack(raw: str) -> bool:
    relative = Path(raw)
    if not raw.strip():
        return False
    if relative.is_absolute():
        return False
    return ".." not in relative.parts


def _python_inside(pack_dir: Path, raw: str) -> Path | None:
    root = pack_dir.resolve()
    try:
        candidate = (pack_dir / raw).resolve()
    except OSError:
        return None
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    if candidate.is_file() and candidate.suffix == ".py":
        return candidate
    return None


def _declared_file(pack_dir: Path, raw: Any) -> Path | None:
    if not isinstance(raw, str) or not _stays_in_pack(raw):
        return None
    return _python_inside(pack_dir, raw)


def _add_filename_matches(tests: Path | None, found: dict[Path, Path]) -> None:
    if tests is None:
        return
    for path in sorted(tests.iterdir()):
        if _is_hidden_filename(path):
            found[path.resolve()] = path


def _add_declared(pack_dir: Path, declared: Any, found: dict[Path, Path]) -> None:
    if not isinstance(declared, list):
        return
    for item in declared:
        path = _declared_file(pack_dir, item)
        if path is not None:
            found.setdefault(path.resolve(), path)


def _hidden_paths(pack_dir: Path, declared: Any) -> list[Path]:
    found: dict[Path, Path] = {}
    _add_filename_matches(_tests_directory(pack_dir), found)
    _add_declared(pack_dir, declared, found)
    return [found[key] for key in sorted(found)]


def _other_test_files(tests: Path, hidden: set[Path]) -> list[Path]:
    others: list[Path] = []
    for path in sorted(tests.iterdir()):
        if not path.is_file() or path.suffix != ".py":
            continue
        if path.resolve() in hidden:
            continue
        others.append(path)
    return others


def _append_hidden(path: Path, visible: set[str], digests: list[str], snippets: list[str]) -> None:
    digests.append(file_digest(path))
    text = suite_text(path)
    append_source_snippets(text, visible, snippets)


def _hidden_suite_pins(
    pack_dir: Path | None,
    declared: Any,
) -> tuple[frozenset[str], tuple[str, ...], list[VSetValidationError]]:
    if pack_dir is None:
        return _EMPTY_DIGESTS, (), []
    pack = Path(pack_dir)
    hidden = _hidden_paths(pack, declared)
    tests = _tests_directory(pack)
    hidden_ids = {path.resolve() for path in hidden}
    visible_paths = _other_test_files(tests, hidden_ids) if tests is not None else []
    digests: list[str] = []
    snippets: list[str] = []
    try:
        visible = visible_lines(visible_paths)
        for path in hidden:
            _append_hidden(path, visible, digests, snippets)
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
    folded = normalize_newlines(value)
    return any(snippet in folded for snippet in snippets)


def _key_leaks(key: Any, digests: frozenset[str], snippets: tuple[str, ...]) -> bool:
    if training_view_key(key) in TRAINING_VIEW_LEAKS:
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


def _declared_hidden_tests(oracle: Any) -> Any:
    if not isinstance(oracle, dict):
        return None
    return oracle.get("hidden_tests")


def _training_view_errors(
    training_view: Any,
    pack_dir: Path | None = None,
    oracle: Any = None,
) -> list[VSetValidationError]:
    if not isinstance(training_view, dict):
        return [
            VSetValidationError(
                "vset.hidden_reasoning_in_training_view",
                "training_view is required and must be an object",
            )
        ]
    digests, snippets, read_errors = _hidden_suite_pins(
        pack_dir, _declared_hidden_tests(oracle)
    )
    if read_errors:
        return read_errors
    if contains_hidden_reasoning_key(training_view):
        return [_leak_error()]
    if _training_view_leaks(training_view, digests, snippets):
        return [_leak_error()]
    return []


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
