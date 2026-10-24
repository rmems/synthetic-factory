"""Case-insensitive folding for training-view leak keys."""

from __future__ import annotations

import re
import sys
import unicodedata
from typing import Any

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_training_view_fold")
    from .vset_constants import normalize_identity
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_training_view_fold"
    )
    from vset_constants import normalize_identity


TRAINING_VIEW_LEAKS = frozenset(
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


def training_view_key(key: Any) -> str:
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


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
