"""Deterministic JSON hashing and tag-count helpers."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from pathlib import Path
from collections import Counter
from typing import Any

_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def normalize_tag(tag: str) -> str:
    """Fold a source tag to its lexical normal form.

    The fold is lexical only: case and separator variants collapse, nothing
    else.  It never assigns meaning to a label.
    """
    return _NON_ALNUM_RE.sub("_", tag.strip().lower()).strip("_")


def canonical_json(value: Any) -> str:
    """Return the stable JSON representation used for output hashes."""
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def tag_identity(value: Any) -> tuple[str, str]:
    """Type-sensitive identity so 1, 1.0, True, and \"1\" stay distinct."""
    return type(value).__name__, canonical_json(value)


def count_tag(
    counts: Counter,
    tag: Any,
    originals: dict[tuple[str, str], Any] | None = None,
) -> None:
    ident = tag_identity(tag)
    counts[ident] += 1
    if originals is None:
        return
    originals.setdefault(ident, tag)


def canonical_json_equal(left: Any, right: Any) -> bool:
    """Compare JSON values without Python's bool/number coercion."""
    try:
        return canonical_json(left) == canonical_json(right)
    except TypeError:
        return False
    except ValueError:
        return False


def reject_json_constant(value: str) -> None:
    """Reject Python-only numeric constants accepted by ``json.loads``."""
    raise ValueError(f"non-standard JSON numeric constant: {value}")


def reject_duplicate_object_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON object key {key!r}")
        value[key] = item
    return value


def load_strict_json(payload: str) -> Any:
    """Decode JSON and reject duplicate keys at every object depth."""
    return json.loads(
        payload,
        object_pairs_hook=reject_duplicate_object_keys,
        parse_constant=reject_json_constant,
    )


def display_source_path(source: Path) -> str:
    """Lossless Unicode spelling of a POSIX path's bytes."""
    return os.fsencode(os.fspath(source)).decode("latin-1")


def hash_value(value: Any) -> str:
    """Hash a parsed value deterministically."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def vocabulary_entropy(counts: Counter | dict[str, int]) -> float:
    """Return the Shannon entropy, in bits, of a tag-use distribution."""
    total = sum(count for count in counts.values() if count > 0)
    if total <= 0:
        return 0.0
    entropy = 0.0
    for count in counts.values():
        entropy = _add_entropy_share(entropy, count, total)
    return round(entropy, 6)


def _add_entropy_share(entropy: float, count: int, total: int) -> float:
    if count <= 0:
        return entropy
    share = count / total
    return entropy - share * math.log2(share)
