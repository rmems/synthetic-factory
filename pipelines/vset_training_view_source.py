"""Hidden-suite bytes and the lines that are specific to those files."""

from __future__ import annotations

import hashlib
import io
import sys
import tokenize
from pathlib import Path

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_training_view_source")
    from .vset_constants import ERR_PAYLOAD_INVALID, VSetValidationError
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_training_view_source"
    )
    from vset_constants import ERR_PAYLOAD_INVALID, VSetValidationError


# The whole hidden file must be at least this long before it is a substring.
# A shorter file is identified by its sha256 only.
_MIN_HIDDEN_SNIPPET = 64
# Lines shorter than this are shared boilerplate (``import unittest``).
_MIN_DISTINCTIVE_LINE = 24


def normalize_newlines(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n")


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


def suite_text(path: Path) -> str:
    raw = _read_suite_bytes(path)
    return normalize_newlines(_decode_suite_source(raw, path.name))


def file_digest(path: Path) -> str:
    return hashlib.sha256(_read_suite_bytes(path)).hexdigest()


def _add_stripped_lines(source: str, lines: set[str]) -> None:
    for line in source.splitlines():
        stripped = line.strip()
        if stripped:
            lines.add(stripped)


def visible_lines(paths: list[Path]) -> set[str]:
    lines: set[str] = set()
    for path in paths:
        _add_stripped_lines(suite_text(path), lines)
    return lines


def _named_suite_line(text: str) -> bool:
    """A hidden-suite name, not a shared ``assertRaises`` or docstring line."""

    if "def test_" in text:
        return True
    return text.startswith("class ")


def _keep_hidden_line(text: str, visible: set[str]) -> bool:
    if len(text) < _MIN_DISTINCTIVE_LINE:
        return False
    if text in visible:
        return False
    return _named_suite_line(text)


def append_source_snippets(source: str, visible: set[str], snippets: list[str]) -> None:
    stripped = source.strip()
    if len(stripped) >= _MIN_HIDDEN_SNIPPET:
        snippets.append(stripped)
    for line in source.splitlines():
        text = line.strip()
        if _keep_hidden_line(text, visible):
            snippets.append(text)


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
